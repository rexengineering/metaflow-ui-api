"""Store workflow information"""
from typing import Dict, List, Union

from prism_api.rexflow.entities.types import (
    Task,
    TaskId,
    Workflow,
    WorkflowInstanceId,
)


class Store:
    data: Dict[
        WorkflowInstanceId,
        Dict[str, Union[Workflow, Dict[TaskId, Task]]]
    ] = {}

    @classmethod
    def add_workflow(cls, workflow: Workflow):
        if workflow.iid in cls.data:
            cls.data[workflow.iid]['workflow'] = workflow
            workflow.tasks = list(cls.data[workflow.iid]['tasks'].values())
        else:
            cls.data[workflow.iid] = {'workflow': workflow, 'tasks': {}}

    @classmethod
    def get_workflow(cls, workflow_id: WorkflowInstanceId) -> Workflow:
        return cls.data[workflow_id]['workflow']

    @classmethod
    def get_workflow_list(
        cls,
        iids: List[WorkflowInstanceId],
    ) -> List[Workflow]:
        return [
            d['workflow']
            for iid, d in cls.data.items()
            if iid in iids
            or iids == []
        ]

    @classmethod
    def delete_workflow(cls, workflow_id: WorkflowInstanceId):
        del cls.data[workflow_id]

    @classmethod
    def add_task(cls, task: Task):
        workflow = cls.get_workflow(task.iid)
        if task.tid not in [t.tid for t in workflow.tasks]:
            workflow.tasks.append(task)
        cls.data[task.iid]['tasks'][task.tid] = task

    @classmethod
    def update_task(cls, task: Task):
        workflow_data = cls.data.get(task.iid)
        if workflow_data and workflow_data['tasks'].get(task.tid):
            cls.data[task.iid]['tasks'][task.tid] = task

    @classmethod
    def get_workflow_tasks(
        cls,
        workflow_id: WorkflowInstanceId,
    ) -> Dict[TaskId, Task]:
        return cls.data[workflow_id]['tasks']

    @classmethod
    def get_task(
        cls,
        workflow_id: WorkflowInstanceId,
        task_id: TaskId,
    ) -> Task:
        return cls.data[workflow_id]['tasks'][task_id]

    @classmethod
    def delete_task(
        cls,
        workflow_id: WorkflowInstanceId,
        task_id: TaskId,
    ) -> None:
        if cls.data.get(workflow_id):
            workflow = cls.data[workflow_id]['workflow']
            task = cls.data[workflow_id]['tasks'][task_id]
            workflow.tasks.remove(task)
            del cls.data[workflow_id]['tasks'][task_id]
