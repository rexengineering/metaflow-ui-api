import abc
import asyncio
import logging
from typing import Dict, List

from gql import Client, gql
from gql.transport.aiohttp import AIOHTTPTransport
from httpx import AsyncClient
from pydantic import validate_arguments

from prism_api import settings
from . import queries
from .entities import types as e
from .entities import wrappers as w


logger = logging.getLogger(__name__)


async def get_deployments() -> Dict[str, List[e.WorkflowDeploymentId]]:
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
        deployment_id: e.WorkflowDeploymentId
    ) -> e.Workflow:
        raise NotImplementedError

    @classmethod
    @abc.abstractmethod
    async def get_instances(
        cls,
        deployment_id: e.WorkflowDeploymentId,
    ) -> List[e.WorkflowInstanceId]:
        raise NotImplementedError

    @abc.abstractmethod
    def __init__(self, workflow: e.Workflow) -> None:
        self.workflow = workflow

    @abc.abstractmethod
    async def get_task_data(
        self,
        task_ids: List[e.TaskId],
    ) -> List[e.Task]:
        raise NotImplementedError

    @abc.abstractmethod
    async def save_task_data(
        self,
        tasks: List[e.Task],
    ) -> List[e.Task]:
        raise NotImplementedError

    @abc.abstractmethod
    async def complete_task(
        self,
        tasks: List[e.Task],
    ) -> List[e.Task]:
        raise NotImplementedError


class REXFlowBridgeGQL(REXFlowBridgeABC):
    @staticmethod
    def get_transport(deployment_id):
        deployment_hash = deployment_id.split('-')[-1]
        host = settings.REXFLOW_HOST.format(deployment_id=deployment_hash)
        transport = AIOHTTPTransport(
            url=host,
        )
        return transport

    @classmethod
    @validate_arguments
    async def start_workflow(
        cls,
        deployment_id: e.WorkflowDeploymentId,
    ) -> e.Workflow:
        async with Client(
            transport=cls.get_transport(deployment_id),
            fetch_schema_from_transport=True,
        ) as session:
            query = gql(queries.START_WORKFLOW_MUTATION)
            params = {
                'createWorkflow': w.CreateWorkflowInstanceInput(
                    graphqlUri=settings.REXUI_CALLBACK_HOST
                ).dict(),
            }

            result = await session.execute(query, variable_values=params)
            logger.info(result)
            payload = w.CreateInstancePayload(
                **result['createInstance'],
            )
            return e.Workflow(
                iid=payload.iid,
                did=payload.did,
                status=e.WorkflowStatus.STARTING,
            )

    @classmethod
    @validate_arguments
    async def get_instances(
        cls,
        deployment_id: e.WorkflowDeploymentId,
    ) -> List[e.WorkflowInstanceId]:
        async with Client(
            transport=cls.get_transport(deployment_id),
            fetch_schema_from_transport=True,
        ) as session:
            query = gql(queries.GET_INSTANCES_QUERY)
            result = await session.execute(query)
            logger.info(result)
            payload = w.GetInstancePayload(**result['getInstances'])

            return [
                instance_info.iid
                for instance_info in payload.iid_list
            ]

    @validate_arguments
    def __init__(self, workflow: e.Workflow) -> None:
        self.workflow = workflow
        self.transport = self.get_transport(workflow.did)

    @validate_arguments
    async def get_task_data(
        self,
        task_ids: List[e.TaskId],
    ) -> List[e.Task]:
        async with Client(
            transport=self.transport,
            fetch_schema_from_transport=True,
        ) as session:
            query = gql(queries.GET_TASK_DATA_QUERY)

            async_tasks = []
            for task_id in task_ids:
                params = w.TaskMutationFormInput(
                    iid=self.workflow.iid,
                    tid=task_id,
                )
                async_tasks.append(session.execute(
                    query,
                    variable_values=params,
                ))

            results = await asyncio.gather(*async_tasks)
            logger.info(results)
            tasks = []
            for result in results:
                task = e.Task(
                    iid=result['tasks']['form']['iid'],
                    tid=result['tasks']['form']['tid'],
                    status=e.TaskStatus.UP,
                    data=[
                        e.TaskFieldData(
                            dataId=field['dataId'],
                            type=field['type'],
                            order=field['order'],
                            label=field['label'],
                            data=field['data'],
                            encrypted=field['encrypted'],
                            validators=[
                                e.Validator(
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
        tasks: List[e.Task],
    ) -> List[e.Task]:
        async with Client(
            transport=self.transport,
            fetch_schema_from_transport=True,
        ) as session:
            query = gql(queries.VALIDATE_TASK_DATA_MUTATION)

            async_tasks = []
            for task in tasks:
                params = {
                    'validateTaskInput': w.TaskMutationValidateInput(
                        iid=self.workflow.iid,
                        tid=task.tid,
                        fields=[
                            w.TaskFieldInput(
                                dataId=field.dataId,
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
            logger.info(results)
            for result in results:
                payload = w.TaskValidatePayload(
                    **result['tasks']['validate'],
                )
                if payload.status != e.OperationStatus.SUCCESS:
                    raise Exception(str(payload.validator_results))
            return tasks

    @validate_arguments
    async def save_task_data(
        self,
        tasks: List[e.Task],
    ) -> List[e.Task]:
        async with Client(
            transport=self.transport,
            fetch_schema_from_transport=True,
        ) as session:
            query = gql(queries.SAVE_TASK_DATA_MUTATION)

            async_tasks = []
            for task in tasks:
                params = {
                    'saveTaskInput': w.TaskMutationSaveInput(
                        iid=self.workflow.iid,
                        tid=task.tid,
                        fields=[
                            w.TaskFieldInput(
                                dataId=field.dataId,
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
            logger.info(results)
            for result in results:
                payload = w.TaskSavePayload(
                    **result['tasks']['save'],
                )
                if payload.status != e.OperationStatus.SUCCESS:
                    raise Exception(str(payload.validator_results))
            return tasks

    @validate_arguments
    async def complete_task(
        self,
        tasks: List[e.Task],
    ) -> List[e.Task]:
        async with Client(
            transport=self.transport,
            fetch_schema_from_transport=True,
        ) as session:
            query = gql(queries.COMPLETE_TASK_MUTATION)

            async_tasks = []
            for task in tasks:
                params = {
                    'completeTaskInput': w.TaskMutationCompleteInput(
                        iid=self.workflow.iid,
                        tid=task.tid,
                    ).dict(),
                }
                async_tasks.append(session.execute(
                    query,
                    variable_values=params,
                ))

            results = await asyncio.gather(*async_tasks)
            logger.info(results)
            for result in results:
                payload = w.TaskCompletePayload(
                    **result['tasks']['complete'],
                )
                if payload.status != e.OperationStatus.SUCCESS:
                    raise Exception
            return tasks
