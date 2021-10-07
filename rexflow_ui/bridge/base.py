import abc
from typing import List

from ..entities.types import (
    ExchangeId,
    Task,
    TaskId,
    Workflow,
    WorkflowDeploymentId,
    WorkflowInstanceId
)
from ..entities.wrappers import TaskOperationResults


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
    async def get_task_exchange_data(
        self,
        xid: ExchangeId,
        reset_values: bool = False,
    ) -> Task:
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
    ) -> TaskOperationResults:
        raise NotImplementedError

    @abc.abstractmethod
    async def validate_task_data(
        self,
        tasks: List[Task],
    ) -> TaskOperationResults:
        raise NotImplementedError

    @abc.abstractmethod
    async def complete_task(
        self,
        tasks: List[Task],
    ) -> TaskOperationResults:
        raise NotImplementedError
