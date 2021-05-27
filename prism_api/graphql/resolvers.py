import logging
from typing import Optional

from ariadne import (
    InterfaceType,
    MutationType,
    ObjectType,
    QueryType,
    UnionType,
)
from graphql.type.definition import GraphQLResolveInfo
from pydantic.decorator import validate_arguments

from .entities.types import Session
from .entities.wrappers import (
    CompleteTaskPayload,
    CompleteTasksInput,
    Problem,
    SaveTaskInput,
    SaveTasksPayload,
    StartWorkflowInput,
    StartWorkflowPayload,
    TaskFilter,
    UpdateStateInput,
    UpdateStatePayload,
    ValidateTaskInput,
    ValidateTasksPayload,
    ValidationProblem,
    WorkflowFilter,
)
from prism_api.rexflow import api as rexflow
from prism_api.rexflow.errors import ValidationError
from prism_api.rexflow.entities.types import (
    OperationStatus,
    Workflow,
)
from prism_api.state_manager import store

logger = logging.getLogger(__name__)


def resolve_problem_interface_type(obj: Problem, *_):
    return obj.resolve_type()


problem_interface = InterfaceType(
    'ProblemInterface',
    resolve_problem_interface_type,
)

task_problems_union = UnionType(
    'TaskProblems',
    resolve_problem_interface_type,
)


query = QueryType()


@query.field('session')
async def resolve_session(_, info: GraphQLResolveInfo):
    request = info.context['request']
    client_id = request.headers.get('client-id', 'anon')
    state = await store.read_raw_state(client_id)
    return Session(
        id=client_id,
        state=state,
    )


class WorkflowResolver:
    def __init__(self, *_):
        pass

    @validate_arguments
    async def active(
        self,
        info,
        filter: WorkflowFilter = None
    ):
        iids = [] if filter is None else filter.ids
        workflows = await rexflow.get_active_workflows(iids)
        return workflows

    async def available(self, *_):
        available_workflows = await rexflow.get_available_workflows()
        return available_workflows


query.set_field('workflows', WorkflowResolver)


workflow_object = ObjectType('Workflow')


@workflow_object.field('tasks')
@validate_arguments
async def resolve_workflow_tasks(
    workflow: Workflow,
    info,
    filter: Optional[TaskFilter] = None,
):
    if filter:
        return [
            task
            for task in workflow.tasks
            if task.tid in filter.ids
            or filter.ids == []
        ]
    else:
        return workflow.tasks


mutation = MutationType()


class StateMutations:
    @validate_arguments
    async def update(self, info, input: UpdateStateInput):
        request = info.context['request']
        client_id = request.headers.get('client-id', 'anon')
        state = await store.save_raw_state(client_id, input.state)
        return UpdateStatePayload(
            status=OperationStatus.SUCCESS,
            state=state,
        )


class SessionMutations:
    def __init__(sel, *_) -> None:
        pass

    async def start(self, _):
        return {
            'status': OperationStatus.SUCCESS,
            'session': {
                'id': '',
                'state': '',
            },
        }

    async def state(self, _):
        return StateMutations()

    async def close(self, _):
        return {
            'status': OperationStatus.SUCCESS,
        }


mutation.set_field('session', SessionMutations)


class TasksMutations:

    @validate_arguments
    async def validate(self, info, input: ValidateTaskInput):
        try:
            tasks = await rexflow.validate_tasks(input.tasks)
        except ValidationError as e:
            errors = []
            for dataId, error in e.errors.items():
                errors.append(ValidationProblem(
                    message=error['message'],
                    iid=e.iid,
                    tid=e.tid,
                    dataId=dataId,
                    validator=error['validator'],
                ))
            return ValidateTasksPayload(
                status=OperationStatus.FAILURE,
                errors=errors,
            )
        return ValidateTasksPayload(
            status=OperationStatus.SUCCESS,
            tasks=tasks,
        )

    @validate_arguments
    async def save(self, info, input: SaveTaskInput):
        try:
            tasks = await rexflow.save_tasks(input.tasks)
        except ValidationError as e:
            errors = []
            for dataId, error in e.errors.items():
                errors.append(ValidationProblem(
                    message=error['message'],
                    iid=e.iid,
                    tid=e.tid,
                    dataId=dataId,
                    validator=error['validator'],
                ))
            return SaveTasksPayload(
                status=OperationStatus.FAILURE,
                errors=errors,
            )
        return SaveTasksPayload(
            status=OperationStatus.SUCCESS,
            tasks=tasks
        )

    @validate_arguments
    async def complete(self, info, input: CompleteTasksInput):
        try:
            tasks = await rexflow.complete_tasks(input.tasks)
        except ValidationError as e:
            errors = []
            for dataId, error in e.errors.items():
                errors.append(ValidationProblem(
                    message=error['message'],
                    iid=e.iid,
                    tid=e.tid,
                    dataId=dataId,
                    validator=error['validator'],
                ))
            return SaveTasksPayload(
                status=OperationStatus.FAILURE,
                errors=errors,
            )
        return CompleteTaskPayload(
            status=OperationStatus.SUCCESS,
            tasks=tasks
        )


class WorkflowMutations:
    def __init__(self, *_) -> None:
        pass

    @validate_arguments
    async def start(self, info, input: StartWorkflowInput):
        logger.info(input)
        workflow = await rexflow.start_workflow(input.did)
        return StartWorkflowPayload(
            status=OperationStatus.SUCCESS,
            iid=workflow.iid,
            workflow=workflow,
        )

    async def tasks(self, info):
        return TasksMutations()


mutation.set_field('workflow', WorkflowMutations)
