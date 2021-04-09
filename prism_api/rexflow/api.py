"""Interface to interact with REXFlow"""
import asyncio
from collections import defaultdict
import itertools
from typing import Dict, List, Union

from pydantic import validate_arguments

from . import entities as e
from .bridge import REXFlowBridgeGQL as REXFlowBridge


class Index:
    data: Dict[
        e.WorkflowInstanceId,
        Dict[str, Union[e.Workflow, Dict]]
    ] = {}

    @classmethod
    def add_workflow(cls, workflow: e.Workflow):
        cls.data[workflow.iid] = {'workflow': workflow, 'tasks': {}}

    @classmethod
    def get_workflow(cls, workflow_id: e.WorkflowInstanceId):
        return cls.data[workflow_id]['workflow']

    @classmethod
    def get_workflow_list(cls):
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
    def get_workflow_tasks(cls, workflow_id: e.WorkflowInstanceId):
        return cls.data[workflow_id]['tasks']

    @classmethod
    def get_task(cls, workflow_id: e.WorkflowInstanceId, task_id: e.TaskId):
        return cls.data[workflow_id]['tasks'][task_id]


async def get_available_workflows() -> List[e.WorkflowDeploymentId]:
    return ['123']


async def start_workflow(
    deployment_id: e.WorkflowDeploymentId,
) -> e.Workflow:
    workflow = await REXFlowBridge.start_workflow(
        deployment_id=deployment_id,
    )
    Index.add_workflow(workflow)
    return workflow


async def _refresh_workflow(workflow: e.Workflow):
    """Refresh a single workflow task"""
    bridge = REXFlowBridge(workflow)
    workflow.tasks = await bridge.get_task_data()


async def refresh_workflows() -> None:
    """Asyncrhonously refresh all workflows tasks"""
    await asyncio.gather(*[
        _refresh_workflow(d['workflow'])
        for d in Index.data.values()
    ])


async def get_active_workflows() -> List[e.Workflow]:
    await refresh_workflows()
    return Index.get_workflow_list()


async def complete_workflow(
    instance_id: e.WorkflowInstanceId,
) -> None:
    Index.delete_workflow(instance_id)


@validate_arguments
async def start_tasks(tasks: List[e.Task]) -> List[e.Task]:
    created_tasks = []
    for task in tasks:
        Index.add_task(task)
        created_tasks.append(task)
    return created_tasks


async def _save_tasks(
    iid: e.WorkflowInstanceId,
    tasks: List[e.TaskInput],
) -> List[e.Task]:
    bridge = REXFlowBridge(Index.get_workflow(iid))
    return await bridge.save_task_data(tasks)


@validate_arguments
async def save_tasks(tasks: List[e.TaskInput]) -> List[e.Task]:
    # This is not the right process
    # input only contains data not other requirements
    workflow_instances = defaultdict(list)
    for task in tasks:
        workflow_instances[task.iid].append(task)
    results = await asyncio.gather(*[
        _save_tasks(iid, tasks)
        for iid, tasks in workflow_instances
    ])

    return list(itertools.chain(*results))


async def _complete_tasks(
    iid: e.WorkflowInstanceId,
    tasks: List[e.Task],
) -> List[e.Task]:
    bridge = REXFlowBridge(Index.get_workflow(iid))
    return await bridge.complete_task(tasks)


async def complete_tasks(
    tasks: List[e.Task],
) -> List[e.Task]:
    workflow_instances = defaultdict(list)
    for task in tasks:
        workflow_instances[task.iid].append(task)
    results = await asyncio.gather(*[
        _complete_tasks(iid, tasks)
        for iid, tasks in workflow_instances
    ])

    return list(itertools.chain(*results))
