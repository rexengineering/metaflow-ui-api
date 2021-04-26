import logging
from typing import Optional

from ariadne import QueryType, MutationType, ObjectType
from pydantic.decorator import validate_arguments

from .entities import wrappers as w
from prism_api.rexflow import api as rexflow
from prism_api.rexflow.entities import types as e

logger = logging.getLogger(__name__)

query = QueryType()


@query.field('session')
async def resolve_session(*_):
    # TODO add model for Session
    return {
        'id': '',
        'state': '',
    }


class WorkflowResolver:
    def __init__(self, *_):
        pass

    async def active(
        self,
        *_,
        filter: w.WorkflowFilter = None
    ):
        # TODO add filters to api
        workflows = await rexflow.get_active_workflows()
        return workflows

    async def available(self, *_):
        available_workflows = await rexflow.get_available_workflows()
        return available_workflows


query.set_field('workflows', WorkflowResolver)


workflow_object = ObjectType('Workflow')


@workflow_object.field('tasks')
@validate_arguments
async def resolve_workflow_tasks(
    workflow: e.Workflow,
    info,
    filter: Optional[w.TaskFilter] = None,
):
    if filter:
        return [
            task
            for task in workflow.tasks
            if (len(filter.ids) == 0 or task.id in filter.ids)
            and (filter.status is None or task.status == filter.status)
        ]
    else:
        return workflow.tasks


mutation = MutationType()


class StateMutations:
    async def update(*_, input):
        return {
            'status': e.OperationStatus.SUCCESS,
            'state': ''
        }


class SessionMutations:
    def __init__(sel, *_) -> None:
        pass

    async def start(self, _):
        return {
            'status': e.OperationStatus.SUCCESS,
            'session': {
                'id': '',
                'state': '',
            },
        }

    async def state(self, _):
        return StateMutations()

    async def close(self, _):
        return {
            'status': e.OperationStatus.SUCCESS,
        }


mutation.set_field('session', SessionMutations)


class TasksMutations:

    @validate_arguments
    async def validate(self, info, input: w.ValidateTaskInput):
        tasks = await rexflow.validate_tasks(input.tasks)
        return w.ValidateTasksPayload(
            status=e.OperationStatus.SUCCESS,
            tasks=tasks,
        )

    @validate_arguments
    async def save(self, info, input: w.SaveTaskInput):
        tasks = await rexflow.save_tasks(input.tasks)
        return w.SaveTasksPayload(
            status=e.OperationStatus.SUCCESS,
            tasks=tasks
        )

    @validate_arguments
    async def complete(self, info, input: w.CompleteTasksInput):
        tasks = await rexflow.complete_tasks(input.tasks)
        return w.CompleteTaskPayload(
            status=e.OperationStatus.SUCCESS,
            tasks=tasks
        )


class WorkflowMutations:
    def __init__(self, *_) -> None:
        pass

    @validate_arguments
    async def start(self, info, input: w.StartWorkflowInput):
        logger.info(input)
        workflow = await rexflow.start_workflow(input.did)
        return w.StartWorkflowPayload(
            status=e.OperationStatus.SUCCESS,
            iid=workflow.iid,
            workflow=workflow,
        )

    async def tasks(self, info):
        return TasksMutations()


mutation.set_field('workflow', WorkflowMutations)
