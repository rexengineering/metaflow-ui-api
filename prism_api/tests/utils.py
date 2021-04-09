import asyncio
from functools import wraps
import json
from typing import List

from pydantic import validate_arguments

from prism_api.state_manager.store.adapters import StoreABC
from prism_api.rexflow import entities
from prism_api.rexflow.bridge import REXFlowBridgeABC


def run_async(f):
    @wraps(f)
    def _run_async(*args, **kwargs):
        result = f(*args, **kwargs)
        if asyncio.iscoroutine(result):
            return asyncio.run(result)
        else:
            return result
    return _run_async


class FakeStore(StoreABC):
    sleep_time = 1.0

    default = {
        'status': 'ok',
    }

    def __init__(self, client_id) -> None:
        self.client_id = client_id
        self.data = None

    async def read(self):
        # Fake some loading process
        await asyncio.sleep(self.sleep_time)
        return self.data or json.dumps(self.default)

    async def save(self, state: str):
        # Fake some saving process
        assert isinstance(state, str)
        self.data = state
        await asyncio.sleep(self.sleep_time)


class FakeREXFlowBridge(REXFlowBridgeABC):
    sleep_time = 0.2

    @classmethod
    @validate_arguments
    async def start_workflow(
        cls,
        deployment_id: entities.WorkflowDeploymentId,
    ) -> entities.Workflow:
        await asyncio.sleep(cls.sleep_time)
        return entities.Workflow(
            did=deployment_id,
            iid='123',
            status=entities.WorkflowStatus.IN_PROGRESS,
        )

    @validate_arguments
    def __init__(self, workflow: entities.Workflow) -> None:
        pass

    @validate_arguments
    async def get_task_data(
        self,
        task_ids: List[entities.TaskId] = [],
    ) -> List[entities.Task]:
        await asyncio.sleep(self.sleep_time)
        if len(task_ids) == 0:
            task_ids = ['1', '2', '3']
        return [
            entities.Task(
                iid='123',
                id=task_id,
                data=[
                    entities.TaskData(
                        id='name',
                        type=entities.DataType.TEXT,
                        order=1,
                    )
                ]
            )
            for task_id in task_ids
        ]

    @validate_arguments
    async def save_task_data(
        self,
        tasks: List[entities.Task],
    ) -> List[entities.Task]:
        await asyncio.sleep(self.sleep_time)
        return tasks

    @validate_arguments
    async def complete_task(
        self,
        tasks: List[entities.Task],
    ) -> List[entities.Task]:
        await asyncio.sleep(self.sleep_time)
        for task in tasks:
            task.status = entities.TaskStatus.FINISHED
        return tasks
