import asyncio
import logging
from urllib.parse import urljoin
from typing import Dict, List

import backoff
from aiohttp.client_exceptions import ClientError
from gql import Client, gql
from gql.client import AsyncClientSession
from gql.transport import aiohttp
from gql.transport.exceptions import TransportError, TransportServerError
from pydantic import validate_arguments

from .. import queries
from .base import REXFlowBridgeABC
from ..entities.types import (
    ErrorDetails,
    MetaData,
    OperationStatus,
    Task,
    TaskFieldData,
    TaskId,
    TaskStatus,
    Validator,
    Workflow,
    WorkflowInstanceInfo,
    WorkflowStatus,
)
from ..entities.wrappers import (
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
from ..errors import (
    BridgeNotReachableError,
    ValidationErrorDetails,
)
from ..schema import schema
from ..settings import (
    LOG_LEVEL,
    REXUI_CALLBACK_HOST,
    REXFLOW_EXECUTION_TIMEOUT,
)


logger = logging.getLogger(__name__)

# aiohttp info logs are too verbose, forcing them to debug level
if LOG_LEVEL != 'DEBUG':
    aiohttp.log.setLevel(logging.WARNING)


class GQLClient:
    def __init__(self, url: str, path: str = '/graphql'):
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
            schema=schema,
            transport=self._get_transport(),
            execute_timeout=REXFLOW_EXECUTION_TIMEOUT,
        )

    @backoff.on_exception(
        backoff.expo,
        TransportServerError,
        max_tries=3,
        logger=logger,
    )
    async def _execute(
        self,
        session: AsyncClientSession,
        query: str,
        params: Dict,
    ) -> Dict:
        try:
            return await session.execute(query, variable_values=params)
        except Exception:
            logger.exception('We had an exception!')
            raise

    async def execute(self, query: str, params: Dict = None) -> Dict:
        client = self._get_client()
        try:
            async with client as session:
                result = await self._execute(session, query, params)
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
                graphqlUri=REXUI_CALLBACK_HOST,
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
    async def update_workflow_data(self) -> Workflow:
        query = gql(queries.GET_WORKFLOW_QUERY)

        client = GQLClient(self.workflow.bridge_url)
        result = await client.execute(
            query,
            {
                'workflowInput': {
                    'iid': self.workflow.iid
                }
            },
        )

        payload = GetInstancePayload(**result['getInstances'])
        instance = payload.iid_list.pop()

        workflow = Workflow(
            did=self.workflow.did,
            iid=instance.iid,
            name=self.workflow.name,
            status=instance.iid_status,
            metadata_dict={
                data.key: data.value
                for data in instance.meta_data
            } if instance.meta_data else {},
            bridge_url=self.workflow.bridge_url,
        )
        self.workflow = workflow
        return workflow

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
