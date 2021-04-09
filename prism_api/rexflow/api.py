"""Interface to interact with REXFlow"""
import asyncio
from collections import defaultdict
import itertools
from typing import List

from pydantic import validate_arguments

from . import entities as e
from .bridge import REXFlowBridgeGQL as REXFlowBridge
from .store import Store


async def get_available_workflows() -> List[e.WorkflowDeploymentId]:
    return ['123']


async def start_workflow(
    deployment_id: e.WorkflowDeploymentId,
) -> e.Workflow:
    workflow = await REXFlowBridge.start_workflow(
        deployment_id=deployment_id,
    )
    Store.add_workflow(workflow)
    return workflow


async def _refresh_workflow(workflow: e.Workflow):
    """Refresh a single workflow task"""
    bridge = REXFlowBridge(workflow)
    tasks = await bridge.get_task_data()
    workflow.tasks = tasks
    Store.data[workflow.iid]['tasks'] = {
        task.id: task
        for task in tasks
    }


async def refresh_workflows() -> None:
    """Asyncrhonously refresh all workflows tasks"""
    await asyncio.gather(*[
        _refresh_workflow(d['workflow'])
        for d in Store.data.values()
    ])


async def get_active_workflows() -> List[e.Workflow]:
    await refresh_workflows()
    return Store.get_workflow_list()


async def complete_workflow(
    instance_id: e.WorkflowInstanceId,
) -> None:
    Store.delete_workflow(instance_id)


@validate_arguments
async def start_tasks(tasks: List[e.Task]) -> List[e.Task]:
    created_tasks = []
    for task in tasks:
        Store.add_task(task)
        created_tasks.append(task)
    return created_tasks


async def _save_tasks(
    iid: e.WorkflowInstanceId,
    tasks: List[e.TaskInput],
) -> List[e.Task]:
    bridge = REXFlowBridge(Store.get_workflow(iid))
    updated_tasks = []
    for task_input in tasks:
        task = Store.get_task(iid, task_input.id)
        task_data = task.get_data_dict()
        for task_data_input in task_input.data:
            task_data[task_data_input.id].data = task_data_input.data
        updated_tasks.append(task)
    return await bridge.save_task_data(updated_tasks)


@validate_arguments
async def save_tasks(tasks: List[e.TaskInput]) -> List[e.Task]:
    workflow_instances = defaultdict(list)
    for task in tasks:
        workflow_instances[task.iid].append(task)
    results = await asyncio.gather(*[
        _save_tasks(iid, tasks)
        for iid, tasks in workflow_instances.items()
    ])

    return list(itertools.chain(*results))


async def _complete_tasks(
    iid: e.WorkflowInstanceId,
    tasks: List[e.TaskInput],
) -> List[e.Task]:
    updated_tasks = await _save_tasks(iid, tasks)
    bridge = REXFlowBridge(Store.get_workflow(iid))
    return await bridge.complete_task(updated_tasks)


@validate_arguments
async def complete_tasks(
    tasks: List[e.TaskInput],
) -> List[e.Task]:
    workflow_instances = defaultdict(list)
    for task in tasks:
        workflow_instances[task.iid].append(task)
    results = await asyncio.gather(*[
        _complete_tasks(iid, tasks)
        for iid, tasks in workflow_instances.items()
    ])

    return list(itertools.chain(*results))
