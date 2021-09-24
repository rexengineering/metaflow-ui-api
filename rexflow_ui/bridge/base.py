import abc
from typing import List

from ..entities.types import (
    Task,
    TaskId,
    Workflow,
    WorkflowDeploymentId,
    WorkflowInstanceId
)


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
    async def update_workflow_data(self) -> Workflow:
        raise NotImplementedError

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
