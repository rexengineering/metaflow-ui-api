import asyncio
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
    WorkflowInstanceInfo,
    WorkflowStatus,
)
from prism_api.rexflow.bridge import REXFlowBridgeABC
from prism_api.rexflow.store import Store, TaskNotFoundError


class FakeREXFlowBridge(REXFlowBridgeABC):
    sleep_time = 0.2

    Store = Store

    @classmethod
    async def get_instances(cls, deployment_id) -> List[WorkflowInstanceInfo]:
        return [WorkflowInstanceInfo(
            iid=MOCK_IID,
            iid_status=WorkflowStatus.RUNNING,
        )]

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
            data=[],
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
        if len(task_ids) == 0:
            tasks_dict = self.Store.get_workflow_tasks(self.workflow.iid)
            if tasks_dict:
                return tasks_dict.values()

        tasks = []
        for tid in task_ids:
            try:
                task = self.Store.get_task(self.workflow.iid, tid)
            except TaskNotFoundError:
                task = Task(
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
                )
            tasks.append(task)
        return tasks

    @validate_arguments
    async def validate_task_data(
        self,
        tasks: List[Task],
    ) -> List[Task]:
        await asyncio.sleep(self.sleep_time)
        return tasks

    @validate_arguments
    async def save_task_data(
        self,
        tasks: List[Task],
    ) -> List[Task]:
        await asyncio.sleep(self.sleep_time)
        return tasks

    @validate_arguments
    async def complete_task(
        self,
        tasks: List[Task],
    ) -> List[Task]:
        await asyncio.sleep(self.sleep_time)
        return tasks
