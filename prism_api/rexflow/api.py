"""Interface to interact with REXFlow"""
import asyncio
import logging
from collections import defaultdict
from typing import List, Optional

from pydantic import validate_arguments

from .bridge import (
    get_deployments,
    REXFlowBridgeGQL as REXFlowBridge,
)
from .entities.types import (
    MetaData,
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
from .errors import BridgeNotReachableError, REXFlowError
from .store import Store, WorkflowNotFoundError
from prism_api import settings
from prism_api.graphql.entities.types import SessionId

logger = logging.getLogger()


async def get_available_workflows(refresh=False) -> List[WorkflowDeployment]:
    deployments = Store.get_deployments()
    if refresh or len(deployments) == 0:
        deployments = await get_deployments()
        Store.save_deployments(deployments)
    return deployments


async def _find_workflow_deployment(
    deployment_id: WorkflowDeploymentId,
) -> Optional[WorkflowDeployment]:
    workflows = await get_available_workflows()
    for workflow in workflows:
        if deployment_id in workflow.deployments:
            return workflow

    return None


async def start_workflow(
    deployment_id: WorkflowDeploymentId,
    workflow_name: str = None,
    metadata: List[MetaData] = [],
) -> Workflow:
    deployment = await _find_workflow_deployment(deployment_id)

    if workflow_name is None:
        workflow_name = deployment.name

    if workflow_name in settings.TALKTRACK_WORKFLOWS:
        metadata.append(MetaData(
            key='type',
            value='talktrack',
        ))

    try:
        workflow = await REXFlowBridge.start_workflow(
            bridge_url=deployment.bridge_url,
            metadata=metadata,
        )
        workflow.name = workflow_name
    except BridgeNotReachableError:
        logger.error('Trying to connect to an unreacheable bridge')
        raise
    Store.add_workflow(workflow)
    # refresh new workflow until running with metadata
    bridge = REXFlowBridge(workflow)
    while workflow.status == WorkflowStatus.STARTING:
        workflow = await bridge.update_workflow_data()
    Store.add_workflow(workflow)
    return workflow


async def start_workflow_by_name(
    workflow_name: str,
    metadata: List[MetaData] = [],
) -> Workflow:
    deployments = await get_available_workflows()
    try:
        deployment_ids = [
            deployment.deployments for deployment in deployments
            if deployment.name == workflow_name
        ].pop()
    except IndexError:
        logger.exception(f'Could not find a deployment for {workflow_name}')
        raise REXFlowError(f'Workflow {workflow_name} cannot be started')

    if deployment_ids:
        # Start first deployment
        return await start_workflow(
            deployment_ids.pop(),
            workflow_name=workflow_name,
            metadata=metadata,
        )
    else:
        logger.error(f'Workflow {workflow_name} cannot be started')
        raise REXFlowError(f'Workflow {workflow_name} cannot be started')


async def _refresh_instance(
    workflow_name: str,
    did: WorkflowDeploymentId,
    bridge_url: str,
):
    try:
        instances = await REXFlowBridge.get_instances(bridge_url)
    except BridgeNotReachableError:
        logger.exception('Trying to connect to an unreacheable bridge')
        instances = []
    for instance in instances:
        workflow = Workflow(
            did=did,
            iid=instance.iid,
            name=workflow_name,
            status=instance.iid_status,
            metadata_dict={
                data.key: data.value
                for data in instance.meta_data
            } if instance.meta_data else {},
            bridge_url=bridge_url,
        )
        Store.add_workflow(workflow)


async def _refresh_instances():
    workflows = await get_available_workflows()
    async_tasks = []
    for workflow in workflows:
        for did in workflow.deployments:
            async_tasks.append(_refresh_instance(
                workflow.name,
                did,
                workflow.bridge_url,
            ))

    await asyncio.gather(*async_tasks)


async def _refresh_workflow(workflow: Workflow):
    """Refresh a single workflow task"""
    bridge = REXFlowBridge(workflow)
    try:
        tasks = await bridge.get_task_data([
            task.tid for task in workflow.tasks
        ])
    except BridgeNotReachableError:
        logger.exception('Trying to connect to the wrong bridge')
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
    session_id: SessionId,
    iids: List[WorkflowInstanceId],
) -> List[Workflow]:
    workflows = [
        workflow
        for workflow in Store.get_workflow_list(iids)
        if workflow.status == WorkflowStatus.RUNNING
        and workflow.metadata_dict.get('session_id') == session_id
    ]

    for workflow in workflows:
        tasks = Store.get_workflow_tasks(workflow.iid)
        workflow.tasks = list(tasks.values())

    return workflows


async def complete_workflow(
    instance_id: WorkflowInstanceId,
) -> None:
    workflow = Store.get_workflow(instance_id)
    workflow.status = WorkflowStatus.COMPLETED
    Store.add_workflow(workflow)


async def cancel_workflow(
    instance_id: WorkflowInstanceId,
) -> bool:
    workflow = Store.get_workflow(instance_id)
    bridge = REXFlowBridge(workflow)
    result = await bridge.cancel_workflow()

    if result:
        workflow.status = WorkflowStatus.CANCELED
        Store.add_workflow(workflow)

    return result


@validate_arguments
async def start_tasks(
    iid: WorkflowInstanceId,
    tasks: List[TaskId]
) -> List[Task]:
    try:
        workflow = Store.get_workflow(iid)
    except WorkflowNotFoundError:
        await _refresh_instances()
        workflow = Store.get_workflow(iid)
    bridge = REXFlowBridge(workflow)
    created_tasks = []
    # Get tasks with initial values
    try:
        created_tasks = await bridge.get_task_data(tasks, reset_values=True)
    except BridgeNotReachableError:
        logger.error('Trying to connect to an unreacheable bridge')
        raise
    # Save initial values
    await bridge.save_task_data(created_tasks)
    for task in created_tasks:
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

    try:
        result = await bridge.validate_task_data(updated_tasks)
    except BridgeNotReachableError:
        logger.exception('Trying to connect to an unreachable bridge')
        result = TaskOperationResults(
            errors=[{'message': 'Unreachable bridge'}]
        )

    return result


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

    try:
        result = await bridge.save_task_data(updated_tasks)
    except BridgeNotReachableError:
        logger.exception('Trying to connect to an unreachable bridge')
        result = TaskOperationResults(
            errors=[{'message': 'Unreachable bridge'}]
        )

    return result


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

    try:
        result = await bridge.complete_task(updated_tasks.successful)
    except BridgeNotReachableError:
        logger.exception('Trying to connect to an unreachable bridge')
        result = TaskOperationResults(
            errors=[{'message': 'Unreachable bridge'}]
        )

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
