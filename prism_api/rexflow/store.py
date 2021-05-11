"""Store workflow information"""
from typing import Dict, List, Union

from prism_api.rexflow.entities import types as e


class Store:
    data: Dict[
        e.WorkflowInstanceId,
        Dict[str, Union[e.Workflow, Dict[e.TaskId, e.Task]]]
    ] = {}

    @classmethod
    def add_workflow(cls, workflow: e.Workflow):
        if workflow.iid in cls.data:
            cls.data[workflow.iid]['workflow'] = workflow
            workflow.tasks = list(cls.data[workflow.iid]['tasks'].values())
        else:
            cls.data[workflow.iid] = {'workflow': workflow, 'tasks': {}}

    @classmethod
    def get_workflow(cls, workflow_id: e.WorkflowInstanceId) -> e.Workflow:
        return cls.data[workflow_id]['workflow']

    @classmethod
    def get_workflow_list(
        cls,
        iids: List[e.WorkflowInstanceId],
    ) -> List[e.Workflow]:
        return [
            d['workflow']
            for iid, d in cls.data.items()
            if iid in iids
            or iids == []
        ]

    @classmethod
    def delete_workflow(cls, workflow_id: e.WorkflowInstanceId):
        del cls.data[workflow_id]

    @classmethod
    def add_task(cls, task: e.Task):
        workflow = cls.get_workflow(task.iid)
        if task.tid not in [t.tid for t in workflow.tasks]:
            workflow.tasks.append(task)
        cls.data[task.iid]['tasks'][task.tid] = task

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
