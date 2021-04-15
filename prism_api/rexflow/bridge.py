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


class REXFlowBridgeABC(abc.ABC):
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
        task_ids: List[e.TaskId] = [],
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
    @validate_arguments
    async def start_workflow(
        cls,
        deployment_id: e.WorkflowDeploymentId,
    ) -> e.Workflow:
        async with Client(
            transport=cls.get_transport(),
            fetch_schema_from_transport=True,
        ) as session:
            query = gql(queries.START_WORKFLOW_MUTATION)
            params = {
                'startWorkflowInput': w.StartWorkflowInput(
                    did=deployment_id,
                ).dict(),
            }

            result = await session.execute(query, variable_values=params)
            logger.info(result)
            payload = w.StartWorkflowPayload(
                **result['workflow']['start'],
            )
            if payload.errors:
                raise Exception(
                    '\n'.join([error.message for error in payload.errors]),
                )
            return payload.workflow

    @validate_arguments
    def __init__(self, workflow: e.Workflow) -> None:
        self.workflow = workflow
        self.endpoint = settings.REXFLOW_HOST_INSTANCE.format(
            instance_id=workflow.iid,
        )
        self.transport = self.get_transport()

    @validate_arguments
    async def get_task_data(
        self,
        task_ids: List[e.TaskId] = [],
    ) -> List[e.Task]:
        async with Client(
            transport=self.transport,
            fetch_schema_from_transport=True,
        ) as session:
            query = gql(queries.GET_TASK_DATA_QUERY)
            if task_ids:
                params = {
                    'taskFilter': w.TaskFilter(
                        ids=task_ids,
                    ).dict(),
                }
            else:
                params = {}

            result = await session.execute(query, variable_values=params)
            logger.info(result)
            all_tasks = []
            for workflow in result['workflows']['active']:
                tasks = [
                    e.Task(iid=workflow['iid'], **task)
                    for task in workflow['tasks']
                ]
                all_tasks.extend(tasks)
            return all_tasks

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
            params = {
                'saveTasksInput': w.SaveTaskInput(
                    tasks=tasks,
                ).dict(),
            }

            result = await session.execute(query, variable_values=params)
            logger.info(result)
            payload = w.SaveTasksPayload(
                **result['workflow']['tasks']['save'],
            )
            if payload.errors:
                raise Exception(
                    '\n'.join([error.message for error in payload.errors]),
                )
            return payload.tasks

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
            params = {
                'completeTasksInput': w.CompleteTasksInput(
                    tasks=tasks,
                ).dict(),
            }

            result = await session.execute(query, variable_values=params)
            logger.info(result)
            payload = w.CompleteTaskPayload(
                **result['workflow']['tasks']['complete'],
            )
            if payload.errors:
                raise Exception(
                    '\n'.join([error.message for error in payload.errors]),
                )
            return payload.tasks


class REXFlowBridgeHTTP(REXFlowBridgeABC):
    _endpoint = settings.REXFLOW_HOST

    @classmethod
    async def get_workflow_catalog(cls) -> list[entities.WorkflowDeploymentId]:
        ...

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
        task_ids: List[e.TaskId] = [],
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
