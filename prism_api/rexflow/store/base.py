"""Abstract base class for Store adapter"""
import abc
from typing import Dict, List

from prism_api.rexflow.entities.types import (
    Task,
    TaskId,
    Workflow,
    WorkflowInstanceId,
)


class StoreABC(abc.ABC):
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
        iids: List[WorkflowInstanceId],
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
