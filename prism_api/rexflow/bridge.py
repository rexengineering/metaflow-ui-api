import abc
import asyncio
import logging
from typing import Dict, List

from aiohttp.client_exceptions import ClientError
from gql import Client, gql
from gql.transport import aiohttp
from gql.transport.exceptions import TransportError
from httpx import AsyncClient, ConnectError
from pydantic import validate_arguments

from . import queries
from .entities.types import (
    ErrorDetails,
    OperationStatus,
    Task,
    TaskFieldData,
    TaskId,
    TaskStatus,
    Validator,
    Workflow,
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


async def get_deployments() -> Dict[str, List[WorkflowDeploymentId]]:
    async with AsyncClient() as client:
        try:
            result = await client.get(
                f'{settings.REXFLOW_FLOWD_HOST}/wf_map',
            )
        except ConnectError as e:
            raise REXFlowNotReachable from e
        result.raise_for_status()
        data = result.json()['wf_map']
        return {
            name: [deployment['id'] for deployment in deployments]
            for name, deployments in data.items()
        }


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


class REXFlowBridgeGQL(REXFlowBridgeABC):
    @staticmethod
    def _get_transport(deployment_id):
        host = settings.REXFLOW_HOST.format(deployment_id=deployment_id)
        transport = aiohttp.AIOHTTPTransport(
            url=host,
        )
        return transport

    @classmethod
    def _get_client(cls, deployment_id):
        return Client(
            transport=cls._get_transport(deployment_id),
            fetch_schema_from_transport=True,
        )

    @classmethod
    @validate_arguments
    async def start_workflow(
        cls,
        deployment_id: WorkflowDeploymentId,
    ) -> Workflow:
        query = gql(queries.START_WORKFLOW_MUTATION)
        params = {
            'createWorkflow': CreateWorkflowInstanceInput(
                graphqlUri=settings.REXUI_CALLBACK_HOST,
            ).dict(),
        }

        client = cls._get_client(deployment_id)
        try:
            async with client as session:
                result = await session.execute(query, variable_values=params)
                logger.debug(result)
        except (ClientError, TransportError) as e:
            raise BridgeNotReachableError from e
        finally:
            await client.transport.close()

        payload = CreateInstancePayload(
            **result['createInstance'],
        )
        return Workflow(
            iid=payload.iid,
            did=payload.did,
            status=WorkflowStatus.STARTING,
        )

    @classmethod
    @validate_arguments
    async def get_instances(
        cls,
        deployment_id: WorkflowDeploymentId,
    ) -> List[WorkflowInstanceInfo]:
        query = gql(queries.GET_INSTANCES_QUERY)

        client = cls._get_client(deployment_id)
        try:
            async with client as session:
                result = await session.execute(query)
                logger.debug(result)
        except (ClientError, TransportError) as e:
            raise BridgeNotReachableError from e
        finally:
            await client.transport.close()

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

        client = self._get_client(self.workflow.did)
        try:
            async with client as session:
                async_tasks = []
                for task_id in task_ids:
                    params = {
                        'formInput': TaskMutationFormInput(
                            iid=self.workflow.iid,
                            tid=task_id,
                            reset=reset_values,
                        ).dict(),
                    }
                    async_tasks.append(session.execute(
                        query,
                        variable_values=params,
                    ))

                results = await asyncio.gather(*async_tasks)
                logger.debug(results)
        except (ClientError, TransportError) as e:
            raise BridgeNotReachableError from e
        finally:
            await client.transport.close()

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
                        encrypted=field['encrypted'],
                        validators=[
                            Validator(
                                type=validator['type'],
                                constraint=validator['constraint'],
                            )
                            for validator in field['validators']
                        ],
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

        client = self._get_client(self.workflow.did)
        try:
            async with client as session:
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
                    async_tasks.append(session.execute(
                        query,
                        variable_values=params,
                    ))

                async_results = await asyncio.gather(*async_tasks)
                logger.debug(async_results)
        except (ClientError, TransportError) as e:
            raise BridgeNotReachableError from e
        finally:
            await client.transport.close()

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

        client = self._get_client(self.workflow.did)
        try:
            async with client as session:
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
                    async_tasks.append(session.execute(
                        query,
                        variable_values=params,
                    ))

                async_results = await asyncio.gather(*async_tasks)
                logger.debug(async_results)
        except (ClientError, TransportError) as e:
            raise BridgeNotReachableError from e
        finally:
            await client.transport.close()

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

        client = self._get_client(self.workflow.did)
        try:
            async with client as session:
                async_tasks = []
                for task in tasks:
                    params = {
                        'completeTaskInput': TaskMutationCompleteInput(
                            iid=self.workflow.iid,
                            tid=task.tid,
                        ).dict(),
                    }
                    async_tasks.append(session.execute(
                        query,
                        variable_values=params,
                    ))

                async_results = await asyncio.gather(*async_tasks)
                logger.debug(async_results)
        except (ClientError, TransportError) as e:
            raise BridgeNotReachableError from e
        finally:
            await client.transport.close()

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

        client = self._get_client(self.workflow.did)
        try:
            async with client as session:
                result = await session.execute(query, variable_values=params)
                logger.debug(result)
        except (ClientError, TransportError) as e:
            raise BridgeNotReachableError from e
        finally:
            await client.transport.close()

        payload = CancelInstancePayload(
            **result['cancelInstance'],
        )

        return payload.status == OperationStatus.SUCCESS
