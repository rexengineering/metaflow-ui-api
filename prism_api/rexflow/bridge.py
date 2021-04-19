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
from .schema import schema


logger = logging.getLogger(__name__)


class REXFlowBridgeABC(abc.ABC):
    @classmethod
    @abc.abstractmethod
    async def get_deployments(cls):
        raise NotImplementedError

    @classmethod
    @abc.abstractmethod
    async def start_workflow(
        cls,
        deployment_id: e.WorkflowDeploymentId
    ) -> e.Workflow:
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
    @classmethod
    def get_transport(cls):
        transport = AIOHTTPTransport(
            url=f'{settings.REXFLOW_HOST}',
        )
        return transport

    @classmethod
    async def get_deployments(cls):
        async with AsyncClient() as client:
            result = await client.get(
                f'{settings.REXFLOW_FLOWD_HOST}/wf_map',
            )
            result.raise_for_status()
            data = result.json()['wf_map']
            return data

    @classmethod
    @validate_arguments
    async def start_workflow(
        cls,
        deployment_id: e.WorkflowDeploymentId,
    ) -> e.Workflow:
        async with Client(
            transport=cls.get_transport(),
            schema=schema,
        ) as session:
            query = gql(queries.START_WORKFLOW_MUTATION)
            params = {
                'deploymentId': deployment_id,
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

    @validate_arguments
    def __init__(self, workflow: e.Workflow) -> None:
        self.workflow = workflow
        self.endpoint = settings.REXFLOW_HOST_INSTANCE.format(
            instance_id=workflow.iid,
        )
        self.transport = AIOHTTPTransport(
            url=self.endpoint,
        )

    @validate_arguments
    async def get_task_data(
        self,
        task_ids: List[e.TaskId],
    ) -> List[e.Task]:
        async with Client(
            transport=self.transport,
            schema=schema,
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
                    status=result['tasks']['form']['status'],
                    data=[
                        e.TaskFieldData(
                            id=field['id'],
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
            schema=schema,
        ) as session:
            query = gql(queries.VALIDATE_TASK_DATA_MUTATION)

            async_tasks = []
            for task in tasks:
                params = {
                    'saveTasksInput': w.TaskMutationValidateInput(
                        iid=self.workflow.iid,
                        tid=task.tid,
                        fields=[
                            w.TaskFieldInput(
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
            schema=schema,
        ) as session:
            query = gql(queries.SAVE_TASK_DATA_MUTATION)

            async_tasks = []
            for task in tasks:
                params = {
                    'saveTasksInput': w.TaskMutationSaveInput(
                        iid=self.workflow.iid,
                        tid=task.tid,
                        fields=[
                            w.TaskFieldInput(
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
            schema=schema,
        ) as session:
            query = gql(queries.COMPLETE_TASK_MUTATION)

            async_tasks = []
            for task in tasks:
                params = {
                    'saveTasksInput': w.TaskMutationCompleteInput(
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


class REXFlowBridgeHTTP(REXFlowBridgeABC):
    _endpoint = settings.REXFLOW_HOST

    @classmethod
    async def get_deployments(cls):
        async with AsyncClient() as client:
            result = await client.get(
                f'{settings.REXFLOW_FLOWD_HOST}/wf_map',
            )
            result.raise_for_status()
            data = result.json()['wf_map']
            return data

    @classmethod
    @validate_arguments
    async def start_workflow(
        cls,
        deployment_id: e.WorkflowDeploymentId,
    ) -> e.Workflow:
        async with AsyncClient() as client:
            result = await client.post(
                f'{cls._endpoint}/workflow/run',
                data={
                    'did': deployment_id
                },
            )
            result.raise_for_status()
            data = result.json()['data']
            return e.Workflow(
                iid=data['instance_id'],
                did=deployment_id,
                status=e.WorkflowStatus.START,
            )

    @validate_arguments
    def __init__(self, workflow: e.Workflow) -> None:
        self.workflow = workflow
        self.endpoint = settings.REXFLOW_HOST_INSTANCE.format(
            instance_id=workflow.iid
        )

    async def _concurrent_calls(
        self,
        endpoint: str,
        datalist: List[Dict],
    ) -> List:
        async with AsyncClient() as client:
            tasks = []
            for data in datalist:
                tasks.append(asyncio.create_task(
                    client.post(
                        endpoint,
                        json=data,
                    )
                ))
            results = await asyncio.gather(*tasks)
            resultlist = []
            for result in results:
                result.raise_for_status()
                resultlist.append(result.json()['data'])

            return resultlist

    @validate_arguments
    async def get_task_data(
        self,
        task_ids: List[e.TaskId],
    ) -> List[e.Task]:
        results = await self._concurrent_calls(
            f'{self.endpoint}/task/form',
            [{
                'task_id': task_id,
            } for task_id in task_ids]
        )

        tasks = [
            e.Task(
                id=task['id'],
                data=task['data'],
                status=task['status'],
            ) for task in results
        ]

        return tasks

    @validate_arguments
    async def save_task_data(
        self,
        tasks: List[e.Task],
    ) -> List[e.Task]:
        results = await self._concurrent_calls(
            f'{self.endpoint}/task/save',
            [task.dict() for task in tasks]
        )

        tasks = [
            e.Task(
                id=task['id'],
                data=task['data'],
                status=task['status'],
            ) for task in results
        ]

        return tasks

    @validate_arguments
    async def complete_task(
        self,
        tasks: List[e.Task],
    ) -> List[e.Task]:
        results = await self._concurrent_calls(
            f'{self.endpoint}/task/complete',
            [{
                'task_id': task.id,
            } for task in tasks]
        )

        tasks = [
            e.Task(
                id=task['id'],
                data=task['data'],
                status=task['status'],
            ) for task in results
        ]

        return tasks
