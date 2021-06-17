"""Store workflow information"""
import logging
from typing import Dict, List, Union

from .base import StoreABC
from .errors import (
    WorkflowNotFoundError,
    TaskNotFoundError,
)
from prism_api.rexflow.entities.types import (
    Task,
    TaskId,
    Workflow,
    WorkflowInstanceId,
)

logger = logging.getLogger(__name__)


class Store(StoreABC):
    _data: Dict[
        WorkflowInstanceId,
        Dict[str, Union[Workflow, Dict[TaskId, Task]]]
    ] = {}

    @classmethod
    def add_workflow(cls, workflow: Workflow):
        if workflow.iid in cls._data:
            cls._data[workflow.iid]['workflow'] = workflow
            workflow.tasks = list(cls._data[workflow.iid]['tasks'].values())
        else:
            cls._data[workflow.iid] = {'workflow': workflow, 'tasks': {}}

    @classmethod
    def get_workflow(cls, workflow_id: WorkflowInstanceId) -> Workflow:
        try:
            return cls._data[workflow_id]['workflow']
        except KeyError as e:
            raise WorkflowNotFoundError from e

    @classmethod
    def get_workflow_list(
        cls,
        iids: List[WorkflowInstanceId] = [],
    ) -> List[Workflow]:
        return [
            d['workflow']
            for iid, d in cls._data.items()
            if iid in iids
            or iids == []
        ]

    @classmethod
    def delete_workflow(cls, workflow_id: WorkflowInstanceId):
        try:
            del cls._data[workflow_id]
        except KeyError:
            logger.exception('Tried to delete unexisting workflow')

    @classmethod
    def add_task(cls, task: Task):
        workflow = cls.get_workflow(task.iid)
        if task.tid not in [t.tid for t in workflow.tasks]:
            workflow.tasks.append(task)
        cls._data[task.iid]['tasks'][task.tid] = task

    @classmethod
    def update_task(cls, task: Task):
        workflow_data = cls._data.get(task.iid)
        if workflow_data and workflow_data['tasks'].get(task.tid):
            cls._data[task.iid]['tasks'][task.tid] = task

    @classmethod
    def get_workflow_tasks(
        cls,
        workflow_id: WorkflowInstanceId,
    ) -> Dict[TaskId, Task]:
        try:
            return cls._data[workflow_id]['tasks']
        except KeyError as e:
            raise WorkflowNotFoundError from e

    @classmethod
    def get_task(
        cls,
        workflow_id: WorkflowInstanceId,
        task_id: TaskId,
    ) -> Task:
        try:
            return cls._data[workflow_id]['tasks'][task_id]
        except KeyError as e:
            raise TaskNotFoundError from e

    @classmethod
    def delete_task(
        cls,
        workflow_id: WorkflowInstanceId,
        task_id: TaskId,
    ) -> None:
        if cls._data.get(workflow_id):
            try:
                workflow = cls._data[workflow_id]['workflow']
            except KeyError as e:
                raise WorkflowNotFoundError from e
            try:
                task = cls._data[workflow_id]['tasks'][task_id]
            except KeyError:
                logger.exception('Tried to delete a task that does not exists')
            workflow.tasks.remove(task)
            del cls._data[workflow_id]['tasks'][task_id]

    @classmethod
    def clear(cls):
        cls._data = {}
