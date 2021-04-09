"""Store workflow information"""
from typing import Dict, List, Union

from prism_api.rexflow import entities as e


class Store:
    data: Dict[
        e.WorkflowInstanceId,
        Dict[str, Union[e.Workflow, Dict[e.TaskId, e.Task]]]
    ] = {}

    @classmethod
    def add_workflow(cls, workflow: e.Workflow):
        cls.data[workflow.iid] = {'workflow': workflow, 'tasks': {}}

    @classmethod
    def get_workflow(cls, workflow_id: e.WorkflowInstanceId) -> e.Workflow:
        return cls.data[workflow_id]['workflow']

    @classmethod
    def get_workflow_list(cls) -> List[e.Workflow]:
        return [
            d['workflow']
            for d in cls.data.values()
        ]

    @classmethod
    def delete_workflow(cls, workflow_id: e.WorkflowInstanceId):
        del cls.data[workflow_id]

    @classmethod
    def add_task(cls, task: e.Task):
        cls.data[task.iid]['tasks'][task.id] = task

    @classmethod
    def get_workflow_tasks(
        cls,
        workflow_id: e.WorkflowInstanceId,
    ) -> Dict[e.TaskId, e.Task]:
        return cls.data[workflow_id]['tasks']

    @classmethod
    def get_task(
        cls,
        workflow_id: e.WorkflowInstanceId,
        task_id: e.TaskId,
    ) -> e.Task:
        return cls.data[workflow_id]['tasks'][task_id]
