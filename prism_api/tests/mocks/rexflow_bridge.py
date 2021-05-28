import asyncio
from prism_api.rexflow.entities.wrappers import TaskOperationResults
from typing import List

from pydantic import validate_arguments

from . import MOCK_IID
from prism_api.rexflow.entities.types import (
    DataType,
    Task,
    TaskFieldData,
    TaskId,
    Validator,
    ValidatorEnum,
    Workflow,
    WorkflowDeploymentId,
    WorkflowStatus,
)
from prism_api.rexflow.bridge import REXFlowBridgeABC
from prism_api.rexflow.store import Store


class FakeREXFlowBridge(REXFlowBridgeABC):
    sleep_time = 0.2

    @classmethod
    async def get_instances(cls, deployment_id):
        return [MOCK_IID]

    @classmethod
    @validate_arguments
    async def start_workflow(
        cls,
        deployment_id: WorkflowDeploymentId,
    ) -> Workflow:
        await asyncio.sleep(cls.sleep_time)
        return Workflow(
            did=deployment_id,
            iid=MOCK_IID,
            status=WorkflowStatus.RUNNING,
            data=Store.data.get(MOCK_IID, {}).get('tasks', [])
        )

    @validate_arguments
    def __init__(self, workflow: Workflow) -> None:
        self.workflow = workflow

    @validate_arguments
    async def get_task_data(
        self,
        task_ids: List[TaskId] = []
    ) -> List[Task]:
        await asyncio.sleep(self.sleep_time)
        if len(task_ids) == 0 and self.workflow.iid in Store.data:
            return Store.data[self.workflow.iid]['tasks'].values()

        tasks = []
        for tid in task_ids:
            if tid in Store.data[self.workflow.iid]['tasks']:
                tasks.append(Store.data[self.workflow.iid]['tasks'][tid])
            else:
                tasks.append(Task(
                    iid=self.workflow.iid,
                    tid=tid,
                    data=[
                        TaskFieldData(
                            dataId='fname',
                            type=DataType.TEXT,
                            order=1,
                            label='First Name',
                            validators=[
                                Validator(
                                    type=ValidatorEnum.REGEX,
                                    constraint=r'.*',
                                )
                            ]
                        )
                    ],
                ))
        return tasks

    @validate_arguments
    async def validate_task_data(
        self,
        tasks: List[Task],
    ) -> TaskOperationResults:
        await asyncio.sleep(self.sleep_time)
        result = TaskOperationResults()
        result.successful = tasks
        return result

    @validate_arguments
    async def save_task_data(
        self,
        tasks: List[Task],
    ) -> TaskOperationResults:
        await asyncio.sleep(self.sleep_time)
        result = TaskOperationResults()
        result.successful = tasks
        return result

    @validate_arguments
    async def complete_task(
        self,
        tasks: List[Task],
    ) -> TaskOperationResults:
        await asyncio.sleep(self.sleep_time)
        result = TaskOperationResults()
        result.successful = tasks
        return result
