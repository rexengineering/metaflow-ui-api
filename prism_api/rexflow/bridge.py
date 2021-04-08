import abc
import asyncio
import logging
from typing import Dict, List

from gql import Client, gql
from gql.transport.aiohttp import AIOHTTPTransport
from httpx import AsyncClient
from pydantic import validate_arguments

from prism_api import settings
from . import entities, queries


logger = logging.getLogger(__name__)


class REXFlowBridgeABC(abc.ABC):
    @classmethod
    @abc.abstractmethod
    async def start_workflow(
        cls,
        deployment_id: entities.WorkflowDeploymentId
    ) -> entities.Workflow:
        raise NotImplementedError

    @abc.abstractmethod
    def __init__(self, workflow: entities.Workflow) -> None:
        self.workflow = workflow

    @abc.abstractmethod
    async def get_task_data(
        self,
        task_ids: List[entities.TaskId],
    ) -> List[entities.Task]:
        raise NotImplementedError

    @abc.abstractmethod
    async def save_task_data(
        self,
        tasks: List[entities.Task],
    ) -> List[entities.Task]:
        raise NotImplementedError

    @abc.abstractmethod
    async def complete_task(
        self,
        tasks: List[entities.Task],
    ) -> List[entities.Task]:
        raise NotImplementedError


class REXFlowBridgeGQL(REXFlowBridgeABC):
    _transport = AIOHTTPTransport(
        url=f'{settings.REXFLOW_HOST}/query',
    )

    @classmethod
    @validate_arguments
    async def start_workflow(
        cls,
        deployment_id: entities.WorkflowDeploymentId,
    ) -> entities.Workflow:
        async with Client(
            transport=cls._transport,
            fetch_schema_from_transport=True,
        ) as session:
            query = gql(queries.START_WORKFLOW_MUTATION)
            params = {
                'startWorkflowInput': entities.StartWorkflowInput(
                    did=deployment_id,
                ).dict(),
            }

            result = await session.execute(query, variable_values=params)
            logger.info(result)
            payload = entities.StartWorkflowPayload(
                **result['workflow']['start'],
            )
            if payload.errors:
                raise Exception(
                    '\n'.join([error.message for error in payload.errors]),
                )
            return payload.workflow

    @validate_arguments
    def __init__(self, workflow: entities.Workflow) -> None:
        self.workflow = workflow
        self.endpoint = settings.REXFLOW_HOST_INSTANCE.format(
            instance_id=workflow.iid,
        )
        self.transport = AIOHTTPTransport(
            url=f'{self.endpoint}/query',
        )

    @validate_arguments
    async def get_task_data(
        self,
        task_ids: List[entities.TaskId] = [],
    ) -> List[entities.Task]:
        async with Client(
            transport=self.transport,
            fetch_schema_from_transport=True,
        ) as session:
            query = gql(queries.GET_TASK_DATA_QUERY)
            if task_ids:
                params = {
                    'taskFilter': entities.TaskFilter(
                        ids=task_ids,
                    ).dict(),
                }
            else:
                params = {}

            result = await session.execute(query, variable_values=params)
            logger.info(result)
            tasks = result['workflow']['active']['tasks']
            return [
                entities.Task(**task)
                for task in tasks
            ]

    @validate_arguments
    async def save_task_data(
        self,
        tasks: List[entities.Task],
    ) -> List[entities.Task]:
        async with Client(
            transport=self.transport,
            fetch_schema_from_transport=True,
        ) as session:
            query = gql(queries.SAVE_TASK_DATA_MUTATION)
            params = {
                'saveTasksInput': entities.SaveTaskInput(
                    tasks=tasks,
                ).dict(),
            }

            result = await session.execute(query, variable_values=params)
            logger.info(result)
            payload = entities.SaveTasksPayload(
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
        tasks: List[entities.Task],
    ) -> List[entities.Task]:
        async with Client(
            transport=self.transport,
            fetch_schema_from_transport=True,
        ) as session:
            query = gql(queries.COMPLETE_TASK_MUTATION)
            params = {
                'completeTasksInput': entities.CompleteTasksInput(
                    tasks=tasks,
                ).dict(),
            }

            result = await session.execute(query, variable_values=params)
            logger.info(result)
            payload = entities.CompleteTaskPayload(
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
        deployment_id: entities.WorkflowDeploymentId,
    ) -> entities.Workflow:
        async with AsyncClient() as client:
            result = await client.post(
                f'{cls._endpoint}/workflow/run',
                data={
                    'did': deployment_id
                },
            )
            result.raise_for_status()
            data = result.json()['data']
            return entities.Workflow(
                iid=data['instance_id'],
                did=deployment_id,
                status=entities.WorkflowStatus.WAITING,
            )

    @validate_arguments
    def __init__(self, workflow: entities.Workflow) -> None:
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
        task_ids: List[entities.TaskId],
    ) -> List[entities.Task]:
        results = await self._concurrent_calls(
            f'{self.endpoint}/task/form',
            [{
                'task_id': task_id,
            } for task_id in task_ids]
        )

        tasks = [
            entities.Task(
                id=task['id'],
                data=task['data'],
                status=task['status'],
            ) for task in results
        ]

        return tasks

    @validate_arguments
    async def save_task_data(
        self,
        tasks: List[entities.Task],
    ) -> List[entities.Task]:
        results = await self._concurrent_calls(
            f'{self.endpoint}/task/save',
            [task.dict() for task in tasks]
        )

        tasks = [
            entities.Task(
                id=task['id'],
                data=task['data'],
                status=task['status'],
            ) for task in results
        ]

        return tasks

    @validate_arguments
    async def complete_task(
        self,
        tasks: List[entities.Task],
    ) -> List[entities.Task]:
        results = await self._concurrent_calls(
            f'{self.endpoint}/task/complete',
            [{
                'task_id': task.id,
            } for task in tasks]
        )

        tasks = [
            entities.Task(
                id=task['id'],
                data=task['data'],
                status=task['status'],
            ) for task in results
        ]

        return tasks
