"""Abstract base class for Store adapter"""
import abc
from typing import Dict, List

from ..entities.types import (
    Task,
    TaskId,
    Workflow,
    WorkflowDeployment,
    WorkflowInstanceId,
)


class StoreABC(abc.ABC):
    @classmethod
    @abc.abstractmethod
    def save_deployments(cls, deployments: List[WorkflowDeployment]):
        raise NotImplementedError

    @classmethod
    @abc.abstractmethod
    def get_deployments(cls) -> List[WorkflowDeployment]:
        raise NotImplementedError

    @classmethod
    @abc.abstractmethod
    def add_workflow(cls, workflow: Workflow):
        raise NotImplementedError

    @classmethod
    @abc.abstractmethod
    def get_workflow(cls, workflow_id: WorkflowInstanceId) -> Workflow:
        raise NotImplementedError

    @classmethod
    @abc.abstractmethod
    def get_workflow_list(
        cls,
        iids: List[WorkflowInstanceId] = [],
    ) -> List[Workflow]:
        raise NotImplementedError

    @classmethod
    @abc.abstractmethod
    def delete_workflow(cls, workflow_id: WorkflowInstanceId):
        raise NotImplementedError

    @classmethod
    @abc.abstractmethod
    def add_task(cls, task: Task):
        raise NotImplementedError

    @classmethod
    @abc.abstractmethod
    def update_task(cls, task: Task):
        """Updates an existing task

        Updates task information if it already exists in storage, but if it
        doesn't exists it does nothing.
        """
        raise NotImplementedError

    @classmethod
    @abc.abstractmethod
    def get_workflow_tasks(
        cls,
        workflow_id: WorkflowInstanceId,
    ) -> Dict[TaskId, Task]:
        raise NotImplementedError

    @classmethod
    @abc.abstractmethod
    def get_task(
        cls,
        workflow_id: WorkflowInstanceId,
        task_id: TaskId,
    ) -> Task:
        raise NotImplementedError

    @classmethod
    @abc.abstractmethod
    def delete_task(
        cls,
        workflow_id: WorkflowInstanceId,
        task_id: TaskId,
    ) -> None:
        raise NotImplementedError
