import asyncio
from rexflow_ui.entities.wrappers import TaskOperationResults
from typing import List

from pydantic import validate_arguments

from . import MOCK_DID, MOCK_IID
from rexflow_ui.entities.types import (
    DataType,
    MetaData,
    Task,
    TaskFieldData,
    TaskId,
    Validator,
    ValidatorEnum,
    Workflow,
    WorkflowInstanceInfo,
    WorkflowStatus,
)
from rexflow_ui.bridge.base import REXFlowBridgeABC
from rexflow_ui.store import Store, TaskNotFoundError


class FakeREXFlowBridge(REXFlowBridgeABC):
    sleep_time = 0.2

    Store = Store

    @classmethod
    async def get_instances(cls, deployment_id) -> List[WorkflowInstanceInfo]:
        return [WorkflowInstanceInfo(
            iid=MOCK_IID,
            iid_status=WorkflowStatus.RUNNING,
            meta_data=[MetaData(
                key='session_id',
                value='anon',
            )]
        )]

    @classmethod
    @validate_arguments
    async def start_workflow(
        cls,
        bridge_url: str,
        metadata: List[MetaData] = [],
    ) -> Workflow:
        await asyncio.sleep(cls.sleep_time)
        workflow = Workflow(
            did=MOCK_DID,
            iid=MOCK_IID,
            status=WorkflowStatus.RUNNING,
            data=[],
            bridge_url=bridge_url,
        )
        workflow.metadata_dict = {
            data.key: data.value
            for data in metadata
        }
        return workflow

    @validate_arguments
    def __init__(self, workflow: Workflow) -> None:
        self.workflow = workflow

    @validate_arguments
    async def update_workflow_data(self) -> Workflow:
        return self.workflow

    @validate_arguments
    async def get_task_data(
        self,
        task_ids: List[TaskId] = [],
        *,
        reset_values: bool = False,
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
                if reset_values:
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

    async def cancel_workflow(self) -> bool:
        await asyncio.sleep(self.sleep_time)
        return True
