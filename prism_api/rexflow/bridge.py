import abc
import asyncio
from collections import defaultdict
import logging
from urllib.parse import urljoin
from typing import List

import backoff
from aiohttp.client_exceptions import (
    ClientError,
    ContentTypeError,
    ServerTimeoutError,
)
from gql import Client, gql
from gql.transport import aiohttp
from gql.transport.exceptions import TransportError
from httpx import AsyncClient, ConnectError
from pydantic import validate_arguments

from . import queries
from .entities.types import (
    ErrorDetails,
    MetaData,
    OperationStatus,
    Task,
    TaskFieldData,
    TaskId,
    TaskStatus,
    Validator,
    Workflow,
    WorkflowDeployment,
    WorkflowDeploymentId,
    WorkflowInstanceId,
    WorkflowInstanceInfo,
    WorkflowStatus,
)
from .entities.wrappers import (
    CancelInstancePayload,
    CancelWorkflowInstanceInput,
    CreateInstancePayload,
    CreateWorkflowInstanceInput,
    GetInstancePayload,
    MetaDataInput,
    TaskCompletePayload,
    TaskFieldInput,
    TaskMutationCompleteInput,
    TaskMutationFormInput,
    TaskMutationSaveInput,
    TaskMutationValidateInput,
    TaskOperationResults,
    TaskSavePayload,
    TaskValidatePayload,
)
from .errors import (
    BridgeNotReachableError,
    REXFlowNotReachable,
    ValidationErrorDetails,
)
from prism_api import settings


logger = logging.getLogger(__name__)

# aiohttp info logs are too verbose, forcing them to debug level
if settings.LOG_LEVEL != 'DEBUG':
    aiohttp.log.setLevel(logging.WARNING)


async def get_deployments() -> List[WorkflowDeployment]:
    async with AsyncClient() as client:
        try:
            result = await client.get(
                f'{settings.REXFLOW_FLOWD_HOST}/wf_map',
            )
        except ConnectError as e:
            raise REXFlowNotReachable from e

    result.raise_for_status()
    data = result.json()['wf_map']

    deployments_info = defaultdict(lambda: {
        'deployment_ids': [],
        'bridge_url': '',
    })
    for name, deployments in data.items():
        for deployment in deployments:
            if 'id' in deployment:
                deployments_info[name]['deployment_ids'].append(
                    deployment['id'],
                )
            elif 'bridge_url' in deployment:
                deployments_info[name]['bridge_url'] = deployment['bridge_url']  # noqa E501

    return [
        WorkflowDeployment(
            name=name,
            deployments=deployment['deployment_ids'],
            bridge_url=deployment['bridge_url'],
        )
        for name, deployment in deployments_info.items()
    ]


class REXFlowBridgeABC(abc.ABC):
    @classmethod
    @abc.abstractmethod
    async def start_workflow(
        cls,
        deployment_id: WorkflowDeploymentId
    ) -> Workflow:
        raise NotImplementedError

    @classmethod
    @abc.abstractmethod
    async def get_instances(
        cls,
        deployment_id: WorkflowDeploymentId,
    ) -> List[WorkflowInstanceId]:
        raise NotImplementedError

    @abc.abstractmethod
    def __init__(self, workflow: Workflow) -> None:
        self.workflow = workflow

    @abc.abstractmethod
    async def get_task_data(
        self,
        task_ids: List[TaskId] = [],
    ) -> List[Task]:
        raise NotImplementedError

    @abc.abstractmethod
    async def save_task_data(
        self,
        tasks: List[Task],
    ) -> List[Task]:
        raise NotImplementedError

    @abc.abstractmethod
    async def complete_task(
        self,
        tasks: List[Task],
    ) -> List[Task]:
        raise NotImplementedError


def backoff_hdlr(details):
    message = ('Backing off {wait:0.1f} seconds after {tries} tries '
               'calling function {target} with args {args} and kwargs '
               '{kwargs}'.format(**details))
    logger.warning(message)


class GQLClient:
    def __init__(self, url: str, path: str = 'graphql/'):
        self.url = url
        self.path = path

    def _get_transport(self):
        if '?' in self.url:
            # Do not set path when url has a query string
            # This is required for mock bridge
            graphql_url = self.url
        else:
            graphql_url = urljoin(self.url, self.path)
        transport = aiohttp.AIOHTTPTransport(
            url=graphql_url,
        )
        return transport

    def _get_client(self):
        return Client(
            transport=self._get_transport(),
            fetch_schema_from_transport=True,
        )

    @backoff.on_exception(
        backoff.expo,
        (
            ContentTypeError,
            ServerTimeoutError,
        ),
        max_tries=7,
        on_backoff=backoff_hdlr,
        logger=logger,
    )
    async def _execute(self, client: Client, query, params) -> dict:
        async with client as session:
            return await session.execute(query, variable_values=params)

    async def execute(self, query: str, params: dict = None) -> dict:
        client = self._get_client()
        try:
            result = await self._execute(client, query, params)
            logger.debug(result)
        except (ClientError, TransportError) as e:
            raise BridgeNotReachableError from e
        finally:
            await client.transport.close()

        return result


class REXFlowBridgeGQL(REXFlowBridgeABC):
    @classmethod
    @validate_arguments
    async def start_workflow(
        cls,
        bridge_url: str,
        metadata: List[MetaData] = [],
    ) -> Workflow:
        query = gql(queries.START_WORKFLOW_MUTATION)
        params = {
            'createWorkflow': CreateWorkflowInstanceInput(
                graphqlUri=settings.REXUI_CALLBACK_HOST,
                meta_data=[
                    MetaDataInput(
                        key=data.key,
                        value=data.value,
                    )
                    for data in metadata
                ],
            ).dict(),
        }

        client = GQLClient(bridge_url)
        result = await client.execute(query, params)

        payload = CreateInstancePayload(
            **result['createInstance'],
        )
        return Workflow(
            iid=payload.iid,
            did=payload.did,
            status=WorkflowStatus.STARTING,
            bridge_url=bridge_url,
        )

    @classmethod
    @validate_arguments
    async def get_instances(
        cls,
        bridge_url: str,
    ) -> List[WorkflowInstanceInfo]:
        query = gql(queries.GET_INSTANCES_QUERY)

        client = GQLClient(bridge_url)
        result = await client.execute(query)

        payload = GetInstancePayload(**result['getInstances'])
        return payload.iid_list

    @validate_arguments
    def __init__(self, workflow: Workflow) -> None:
        self.workflow = workflow

    @validate_arguments
    async def get_task_data(
        self,
        task_ids: List[TaskId] = [],
        *,
        reset_values: bool = False
    ) -> List[Task]:
        if len(task_ids) == 0:
            return []

        query = gql(queries.GET_TASK_DATA_QUERY)

        client = GQLClient(self.workflow.bridge_url)

        async_tasks = []
        for task_id in task_ids:
            params = {
                'formInput': TaskMutationFormInput(
                    iid=self.workflow.iid,
                    tid=task_id,
                    reset=reset_values,
                ).dict(),
            }
            async_tasks.append(client.execute(
                query,
                params,
            ))

        results = await asyncio.gather(*async_tasks)

        tasks = []
        for result in results:
            task = Task(
                iid=result['tasks']['form']['iid'],
                tid=result['tasks']['form']['tid'],
                status=TaskStatus.UP,
                data=[
                    TaskFieldData(
                        dataId=field['dataId'],
                        type=field['type'],
                        order=field['order'],
                        label=field['label'],
                        data=field['data'],
                        variant=field['variant'],
                        encrypted=field['encrypted'],
                        validators=[
                            Validator(
                                type=validator['type'],
                                constraint=validator['constraint'],
                            )
                            for validator in field['validators']
                        ] if field['validators'] else [],
                    )
                    for field in result['tasks']['form']['fields']
                ]
            )
            tasks.append(task)
        return tasks

    @validate_arguments
    async def validate_task_data(
        self,
        tasks: List[Task],
    ) -> TaskOperationResults:
        query = gql(queries.VALIDATE_TASK_DATA_MUTATION)

        client = GQLClient(self.workflow.bridge_url)
        async_tasks = []
        for task in tasks:
            params = {
                'validateTaskInput': TaskMutationValidateInput(
                    iid=self.workflow.iid,
                    tid=task.tid,
                    fields=[
                        TaskFieldInput(
                            dataId=field.data_id,
                            data=field.data,
                        )
                        for field in task.data
                    ],
                ).dict(),
            }
            async_tasks.append(client.execute(
                query,
                params,
            ))

        async_results = await asyncio.gather(*async_tasks)

        tasks_dict = {task.tid: task for task in tasks}
        results = TaskOperationResults()
        for result in async_results:
            payload = TaskValidatePayload(
                **result['tasks']['validate'],
            )
            if payload.status != OperationStatus.SUCCESS:
                results.errors.append(ErrorDetails(message=str(payload)))
            elif not payload.passed:
                results.errors.append(
                    ValidationErrorDetails(payload=payload)
                )
            else:
                results.successful.append(tasks_dict[payload.tid])

        return results

    @validate_arguments
    async def save_task_data(
        self,
        tasks: List[Task],
    ) -> TaskOperationResults:
        query = gql(queries.SAVE_TASK_DATA_MUTATION)

        client = GQLClient(self.workflow.bridge_url)
        async_tasks = []
        for task in tasks:
            params = {
                'saveTaskInput': TaskMutationSaveInput(
                    iid=self.workflow.iid,
                    tid=task.tid,
                    fields=[
                        TaskFieldInput(
                            dataId=field.data_id,
                            data=field.data,
                        )
                        for field in task.data
                    ],
                ).dict(),
            }
            async_tasks.append(client.execute(
                query,
                params,
            ))

        async_results = await asyncio.gather(*async_tasks)

        tasks_dict = {task.tid: task for task in tasks}
        results = TaskOperationResults()
        for result in async_results:
            payload = TaskSavePayload(
                **result['tasks']['save'],
            )
            if payload.status != OperationStatus.SUCCESS:
                results.errors.append(ErrorDetails(message=str(payload)))
            elif not payload.passed:
                results.errors.append(
                    ValidationErrorDetails(payload=payload)
                )
            else:
                results.successful.append(tasks_dict[payload.tid])

        return results

    @validate_arguments
    async def complete_task(
        self,
        tasks: List[Task],
    ) -> TaskOperationResults:
        query = gql(queries.COMPLETE_TASK_MUTATION)

        client = GQLClient(self.workflow.bridge_url)
        async_tasks = []
        for task in tasks:
            params = {
                'completeTaskInput': TaskMutationCompleteInput(
                    iid=self.workflow.iid,
                    tid=task.tid,
                ).dict(),
            }
            async_tasks.append(client.execute(
                query,
                params,
            ))

        async_results = await asyncio.gather(*async_tasks)

        tasks_dict = {task.tid: task for task in tasks}
        results = TaskOperationResults()
        for result in async_results:
            payload = TaskCompletePayload(
                **result['tasks']['complete'],
            )
            if payload.status != OperationStatus.SUCCESS:
                results.errors.append(ErrorDetails(message=str(payload)))
            else:
                results.successful.append(tasks_dict[payload.tid])

        return results

    @validate_arguments
    async def cancel_workflow(self) -> bool:
        query = gql(queries.CANCEL_WORKFLOW_QUERY)
        params = {
            'cancelWorkflow': CancelWorkflowInstanceInput(
                iid=self.workflow.iid,
            ).dict(),
        }

        client = GQLClient(self.workflow.bridge_url)
        result = await client.execute(query, params)

        payload = CancelInstancePayload(
            **result['cancelInstance'],
        )

        return payload.status == OperationStatus.SUCCESS
