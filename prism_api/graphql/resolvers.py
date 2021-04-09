import logging
from typing import Optional

from ariadne import QueryType, MutationType, ObjectType
from pydantic.decorator import validate_arguments

from prism_api.rexflow import entities as e
from prism_api.rexflow import api as rexflow

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
        filter: e.WorkflowFilter = None
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
    filter: Optional[e.TaskFilter] = None,
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
    async def start(self, info, input: e.StartTasksInput):
        tasks = await rexflow.start_tasks([
            task_input.to_task()
            for task_input in input.tasks
        ])
        return e.StartTasksPayload(
            status=e.OperationStatus.SUCCESS,
            tasks=tasks,
        )

    @validate_arguments
    async def validate(self, info, input: e.ValidateTaskInput):
        # TODO add validation query
        return e.ValidateTasksPayload(
            status=e.OperationStatus.SUCCESS,
            tasks=[
                e.Task(
                    iid='123',
                    id='123',
                    status=e.TaskStatus.IN_PROGRESS,
                )
            ]
        )

    @validate_arguments
    async def save(self, info, input: e.SaveTaskInput):
        tasks = await rexflow.save_tasks(input.tasks)
        return e.SaveTasksPayload(
            status=e.OperationStatus.SUCCESS,
            tasks=tasks
        )

    @validate_arguments
    async def complete(self, info, input: e.CompleteTasksInput):
        tasks = await rexflow.complete_tasks(input.tasks)
        return e.CompleteTaskPayload(
            status=e.OperationStatus.SUCCESS,
            tasks=tasks
        )


class WorkflowMutations:
    def __init__(self, *_) -> None:
        pass

    @validate_arguments
    async def start(self, info, input: e.StartWorkflowInput):
        logger.info(input)
        workflow = await rexflow.start_workflow(input.did)
        return e.StartWorkflowPayload(
            status=e.OperationStatus.SUCCESS,
            iid=workflow.iid,
            workflow=workflow,
        )

    @validate_arguments
    async def complete(self, info, input: e.CompleteWorkflowInput):
        logger.info(input)
        await rexflow.complete_workflow(input.iid)
        return e.CompleteWorkflowPayload(
            status=e.OperationStatus.SUCCESS,
            iid=input.iid
        )

    async def tasks(self, info):
        return TasksMutations()


mutation.set_field('workflow', WorkflowMutations)
