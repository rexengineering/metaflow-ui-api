import asyncio
from functools import wraps
import json
from typing import List

from pydantic import validate_arguments

from prism_api.state_manager.store.adapters import StoreABC
from prism_api.rexflow.entities import types as e
from prism_api.rexflow.bridge import REXFlowBridgeABC
from prism_api.rexflow.store import Store


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

    test_iid = 'process-123-456'

    @classmethod
    async def get_instances(cls, deployment_id):
        return [cls.test_iid]

    @classmethod
    @validate_arguments
    async def start_workflow(
        cls,
        deployment_id: e.WorkflowDeploymentId,
    ) -> e.Workflow:
        await asyncio.sleep(cls.sleep_time)
        return e.Workflow(
            did=deployment_id,
            iid=cls.test_iid,
            status=e.WorkflowStatus.RUNNING,
            data=Store.data.get(cls.test_iid, {}).get('tasks', [])
        )

    @validate_arguments
    def __init__(self, workflow: e.Workflow) -> None:
        self.workflow = workflow

    @validate_arguments
    async def get_task_data(
        self,
        task_ids: List[e.TaskId]
    ) -> List[e.Task]:
        await asyncio.sleep(self.sleep_time)
        tasks = []
        for tid in task_ids:
            if tid in Store.data[self.workflow.iid]['tasks']:
                tasks.append(Store.data[self.workflow.iid]['tasks'][tid])
            else:
                tasks.append(e.Task(
                    iid=self.workflow.iid,
                    tid=tid,
                    data=[
                        e.TaskFieldData(
                            id='fname',
                            type=e.DataType.TEXT,
                            order=1,
                            label='First Name',
                            validators=[
                                e.Validator(
                                    type=e.ValidatorEnum.REGEX,
                                    constraint=r'.*',
                                )
                            ]
                        )
                    ],
                ))
        return tasks

    @validate_arguments
    async def save_task_data(
        self,
        tasks: List[e.Task],
    ) -> List[e.Task]:
        await asyncio.sleep(self.sleep_time)
        return tasks

    @validate_arguments
    async def complete_task(
        self,
        tasks: List[e.Task],
    ) -> List[e.Task]:
        await asyncio.sleep(self.sleep_time)
        for task in tasks:
            task.status = e.TaskStatus.DOWN
        return tasks
