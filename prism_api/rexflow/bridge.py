import abc
import asyncio
import logging
from typing import Dict, List

from gql import Client, gql
from gql.transport import aiohttp
from httpx import AsyncClient
from pydantic import validate_arguments

from . import queries
from .entities.types import (
    OperationStatus,
    Task,
    TaskFieldData,
    TaskId,
    TaskStatus,
    Validator,
    Workflow,
    WorkflowDeploymentId,
    WorkflowInstanceId,
    WorkflowStatus,
)
from .entities.wrappers import (
    CreateInstancePayload,
    CreateWorkflowInstanceInput,
    GetInstancePayload,
    TaskCompletePayload,
    TaskFieldInput,
    TaskMutationCompleteInput,
    TaskMutationFormInput,
    TaskMutationSaveInput,
    TaskMutationValidateInput,
    TaskSavePayload,
    TaskValidatePayload,
)
from prism_api import settings


logger = logging.getLogger(__name__)

# aiohttp info logs are too verbose, forcing them to debug level
if settings.LOG_LEVEL != 'DEBUG':
    aiohttp.log.setLevel(logging.WARNING)


async def get_deployments() -> Dict[str, List[WorkflowDeploymentId]]:
    async with AsyncClient() as client:
        result = await client.get(
            f'{settings.REXFLOW_FLOWD_HOST}/wf_map',
        )
        result.raise_for_status()
        data = result.json()['wf_map']
        return data


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
    def get_transport(deployment_id):
        host = settings.REXFLOW_HOST.format(deployment_id=deployment_id)
        transport = aiohttp.AIOHTTPTransport(
            url=host,
        )
        return transport

    @classmethod
    @validate_arguments
    async def start_workflow(
        cls,
        deployment_id: WorkflowDeploymentId,
    ) -> Workflow:
        async with Client(
            transport=cls.get_transport(deployment_id),
            fetch_schema_from_transport=True,
        ) as session:
            query = gql(queries.START_WORKFLOW_MUTATION)
            params = {
                'createWorkflow': CreateWorkflowInstanceInput(
                    graphqlUri=settings.REXUI_CALLBACK_HOST
                ).dict(),
            }

            result = await session.execute(query, variable_values=params)
            logger.debug(result)
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
    ) -> List[WorkflowInstanceId]:
        async with Client(
            transport=cls.get_transport(deployment_id),
            fetch_schema_from_transport=True,
        ) as session:
            query = gql(queries.GET_INSTANCES_QUERY)
            result = await session.execute(query)
            logger.debug(result)
            payload = GetInstancePayload(**result['getInstances'])

            return [
                instance_info.iid
                for instance_info in payload.iid_list
                if instance_info.iid_status == WorkflowStatus.RUNNING
            ]

    @validate_arguments
    def __init__(self, workflow: Workflow) -> None:
        self.workflow = workflow
        self.transport = self.get_transport(workflow.did)

    @validate_arguments
    async def get_task_data(
        self,
        task_ids: List[TaskId] = [],
    ) -> List[Task]:
        async with Client(
            transport=self.transport,
            fetch_schema_from_transport=True,
        ) as session:
            if len(task_ids) == 0:
                return []

            query = gql(queries.GET_TASK_DATA_QUERY)

            async_tasks = []
            for task_id in task_ids:
                params = {
                    'formInput': TaskMutationFormInput(
                        iid=self.workflow.iid,
                        tid=task_id,
                    ).dict(),
                }
                async_tasks.append(session.execute(
                    query,
                    variable_values=params,
                ))

            results = await asyncio.gather(*async_tasks)
            logger.debug(results)
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
    ) -> List[Task]:
        async with Client(
            transport=self.transport,
            fetch_schema_from_transport=True,
        ) as session:
            query = gql(queries.VALIDATE_TASK_DATA_MUTATION)

            async_tasks = []
            for task in tasks:
                params = {
                    'validateTaskInput': TaskMutationValidateInput(
                        iid=self.workflow.iid,
                        tid=task.tid,
                        fields=[
                            TaskFieldInput(
                                **field.dict(by_alias=True)
                            )
                            for field in task.data
                        ],
                    ).dict(),
                }
                async_tasks.append(session.execute(
                    query,
                    variable_values=params,
                ))

            results = await asyncio.gather(*async_tasks)
            logger.debug(results)
            for result in results:
                payload = TaskValidatePayload(
                    **result['tasks']['validate'],
                )
                if payload.status != OperationStatus.SUCCESS:
                    raise Exception(str(payload.validator_results))
            return tasks

    @validate_arguments
    async def save_task_data(
        self,
        tasks: List[Task],
    ) -> List[Task]:
        async with Client(
            transport=self.transport,
            fetch_schema_from_transport=True,
        ) as session:
            query = gql(queries.SAVE_TASK_DATA_MUTATION)

            async_tasks = []
            for task in tasks:
                params = {
                    'saveTaskInput': TaskMutationSaveInput(
                        iid=self.workflow.iid,
                        tid=task.tid,
                        fields=[
                            TaskFieldInput(
                                **field.dict(by_alias=True)
                            )
                            for field in task.data
                        ],
                    ).dict(),
                }
                async_tasks.append(session.execute(
                    query,
                    variable_values=params,
                ))

            results = await asyncio.gather(*async_tasks)
            logger.debug(results)
            for result in results:
                payload = TaskSavePayload(
                    **result['tasks']['save'],
                )
                if payload.status != OperationStatus.SUCCESS:
                    raise Exception(str(payload.validator_results))
            return tasks

    @validate_arguments
    async def complete_task(
        self,
        tasks: List[Task],
    ) -> List[Task]:
        async with Client(
            transport=self.transport,
            fetch_schema_from_transport=True,
        ) as session:
            query = gql(queries.COMPLETE_TASK_MUTATION)

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

            results = await asyncio.gather(*async_tasks)
            logger.debug(results)
            for result in results:
                payload = TaskCompletePayload(
                    **result['tasks']['complete'],
                )
                if payload.status != OperationStatus.SUCCESS:
                    raise Exception
            return tasks
