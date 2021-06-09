"""Interface to interact with REXFlow"""
import asyncio
from collections import defaultdict
import logging
from typing import List

from graphql.error.graphql_error import GraphQLError
from pydantic import validate_arguments

from .bridge import (
    get_deployments,
    REXFlowBridgeGQL as REXFlowBridge,
)
from .entities.types import (
    Task,
    TaskId,
    Workflow,
    WorkflowDeployment,
    WorkflowDeploymentId,
    WorkflowInstanceId,
    WorkflowStatus,
)
from .entities.wrappers import (
    TaskChange,
    TaskOperationResults
)
from .store import Store

logger = logging.getLogger()


async def get_available_workflows() -> List[WorkflowDeployment]:
    deployments = await get_deployments()
    return [
        WorkflowDeployment(
            name=name,
            deployments=deployment_ids,
        )
        for name, deployment_ids in deployments.items()
    ]


async def start_workflow(
    deployment_id: WorkflowDeploymentId,
) -> Workflow:
    workflow = await REXFlowBridge.start_workflow(
        deployment_id=deployment_id,
    )
    Store.add_workflow(workflow)
    return workflow


async def _refresh_instance(did: WorkflowDeploymentId):
    instances = await REXFlowBridge.get_instances(did)
    for instance in instances:
        workflow = Workflow(
            did=did,
            iid=instance.iid,
            status=instance.iid_status,
        )
        Store.add_workflow(workflow)


async def _refresh_instances():
    deployment_ids = await get_deployments()
    async_tasks = []
    for deployments in deployment_ids.values():
        for did in deployments:
            async_tasks.append(_refresh_instance(did))

    await asyncio.gather(*async_tasks)


async def _refresh_workflow(workflow: Workflow):
    """Refresh a single workflow task"""
    try:
        bridge = REXFlowBridge(workflow)
        tasks = await bridge.get_task_data([
            task.tid for task in workflow.tasks
        ])
    except GraphQLError:
        Store.delete_workflow(workflow.iid)
    else:
        workflow.tasks = []
        for task in tasks:
            Store.add_task(task)


async def refresh_workflows() -> None:
    """Asyncrhonously refresh all workflows tasks"""
    await _refresh_instances()
    await asyncio.gather(*[
        _refresh_workflow(workflow)
        for workflow in Store.get_workflow_list()
    ])


async def get_active_workflows(
    iids: List[WorkflowInstanceId],
) -> List[Workflow]:
    await refresh_workflows()
    return [
        workflow
        for workflow in Store.get_workflow_list(iids)
        if workflow.status == WorkflowStatus.RUNNING
    ]


async def complete_workflow(
    instance_id: WorkflowInstanceId,
) -> None:
    workflow = Store.get_workflow(instance_id)
    workflow.status = WorkflowStatus.COMPLETED
    Store.add_workflow(workflow)


@validate_arguments
async def start_tasks(
    iid: WorkflowInstanceId,
    tasks: List[TaskId]
) -> List[Task]:
    await refresh_workflows()
    created_tasks = []
    for tid in tasks:
        task = await get_task(iid, tid)
        created_tasks.append(task)
        Store.add_task(task)
    return created_tasks


@validate_arguments
async def get_task(iid: WorkflowInstanceId, tid: TaskId) -> Task:
    bridge = REXFlowBridge(Store.get_workflow(iid))
    task = (await bridge.get_task_data([tid])).pop()
    Store.update_task(task)
    return task


async def _validate_tasks(
    iid: WorkflowInstanceId,
    tasks: List[TaskChange],
) -> TaskOperationResults:
    bridge = REXFlowBridge(Store.get_workflow(iid))
    updated_tasks = []
    for task_input in tasks:
        task = Store.get_task(iid, task_input.tid)
        task_data = task.get_data_dict()
        for task_data_input in task_input.data:
            task_data[task_data_input.dataId].data = task_data_input.data
        updated_tasks.append(task)
    return await bridge.validate_task_data(updated_tasks)


@validate_arguments
async def validate_tasks(tasks: List[TaskChange]) -> TaskOperationResults:
    workflow_instances = defaultdict(list)
    for task in tasks:
        workflow_instances[task.iid].append(task)
    results = await asyncio.gather(*[
        _validate_tasks(iid, tasks)
        for iid, tasks in workflow_instances.items()
    ])

    final_result = TaskOperationResults()
    for result in results:
        final_result.successful.extend(result.successful)
        final_result.errors.extend(result.errors)

    return final_result


async def _save_tasks(
    iid: WorkflowInstanceId,
    tasks: List[TaskChange],
) -> TaskOperationResults:
    bridge = REXFlowBridge(Store.get_workflow(iid))
    updated_tasks = []
    for task_input in tasks:
        task = Store.get_task(iid, task_input.tid)
        task_data = task.get_data_dict()
        for task_data_input in task_input.data:
            task_data[task_data_input.dataId].data = task_data_input.data
        updated_tasks.append(task)
    return await bridge.save_task_data(updated_tasks)


@validate_arguments
async def save_tasks(tasks: List[TaskChange]) -> TaskOperationResults:
    workflow_instances = defaultdict(list)
    for task in tasks:
        workflow_instances[task.iid].append(task)
    results = await asyncio.gather(*[
        _save_tasks(iid, tasks)
        for iid, tasks in workflow_instances.items()
    ])

    final_result = TaskOperationResults()
    for result in results:
        final_result.successful.extend(result.successful)
        final_result.errors.extend(result.errors)

    return final_result


async def _complete_tasks(
    iid: WorkflowInstanceId,
    tasks: List[TaskChange],
) -> TaskOperationResults:
    updated_tasks = await _save_tasks(iid, tasks)
    bridge = REXFlowBridge(Store.get_workflow(iid))
    result = await bridge.complete_task(updated_tasks.successful)
    result.errors.extend(updated_tasks.errors)
    for task in result.successful:
        Store.delete_task(iid, task.tid)
    return result


@validate_arguments
async def complete_tasks(
    tasks: List[TaskChange],
) -> TaskOperationResults:
    workflow_instances = defaultdict(list)
    for task in tasks:
        logger.info(
            f'Complete task {task.tid} on instance {task.iid}'
        )
        workflow_instances[task.iid].append(task)
    results = await asyncio.gather(*[
        _complete_tasks(iid, tasks)
        for iid, tasks in workflow_instances.items()
    ])

    final_result = TaskOperationResults()
    for result in results:
        final_result.successful.extend(result.successful)
        final_result.errors.extend(result.errors)

    return final_result
