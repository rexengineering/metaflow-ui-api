import asyncio
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
    ActivateTalkTrackInput,
    ActivateTalkTrackPayload,
    CompleteTaskPayload,
    CompleteTasksInput,
    FinishTalkTrackInput,
    FinishTalkTrackPayload,
    GenericProblem,
    Problem,
    SaveTaskInput,
    SaveTasksPayload,
    StartTalkTrackInput,
    StartTalkTrackPayload,
    StartWorkflowInput,
    StartWorkflowPayload,
    TaskFilter,
    UpdateStateInput,
    UpdateStatePayload,
    ValidateTaskInput,
    ValidateTasksPayload,
    ValidationProblem,
    ServiceNotAvailableProblem,
    WorkflowFilter,
)
from prism_api import settings
from prism_api.rexflow import api as rexflow
from prism_api.rexflow.errors import (
    BridgeNotReachableError,
    REXFlowError,
    ValidationErrorDetails,
)
from prism_api.rexflow.entities.types import (
    OperationStatus,
    Workflow,
)
from prism_api.state_manager import store
from prism_api.talktrack import actions as talktrack_actions

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
    session_id = request.headers.get(settings.SESSION_ID_HEADER, 'anon')
    state = await store.read_raw_state(session_id)
    return Session(
        id=session_id,
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


class TalkTrackResolver:
    def __init__(self, *_):
        pass

    async def all(self, _):
        return talktrack_actions.list_talktracks()

    async def active(self, info):
        request = info.context['request']
        session_id = request.headers.get(settings.SESSION_ID_HEADER, 'anon')
        return talktrack_actions.get_talktrack_queue(session_id)


query.set_field('talktracks', TalkTrackResolver)

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
        session_id = request.headers.get(settings.SESSION_ID_HEADER, 'anon')
        state = await store.save_raw_state(session_id, input.state)
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
            result = await rexflow.validate_tasks(input.tasks)
        except REXFlowError as e:
            return SaveTasksPayload(
                status=OperationStatus.FAILURE,
                errors=[GenericProblem(message=e)],
            )

        errors = []
        for error in result.errors:
            if isinstance(error, ValidationErrorDetails):
                for dataId, validation_error in error.errors.items():
                    errors.append(ValidationProblem(
                        message=validation_error['message'],
                        iid=error.iid,
                        tid=error.tid,
                        dataId=dataId,
                        validator=validation_error['validator'],
                    ))
            else:
                errors.append(GenericProblem(str(error)))

        if errors:
            status = OperationStatus.FAILURE
        else:
            status = OperationStatus.SUCCESS

        return ValidateTasksPayload(
            status=status,
            tasks=result.successful,
            errors=errors
        )

    @validate_arguments
    async def save(self, info, input: SaveTaskInput):
        try:
            result = await rexflow.save_tasks(input.tasks)
        except REXFlowError as e:
            return SaveTasksPayload(
                status=OperationStatus.FAILURE,
                errors=[GenericProblem(message=e)],
            )

        errors = []
        for error in result.errors:
            if isinstance(error, ValidationErrorDetails):
                for dataId, validation_error in error.errors.items():
                    errors.append(ValidationProblem(
                        message=validation_error['message'],
                        iid=error.iid,
                        tid=error.tid,
                        dataId=dataId,
                        validator=validation_error['validator'],
                    ))
            else:
                errors.append(GenericProblem(str(error)))

        if errors:
            status = OperationStatus.FAILURE
        else:
            status = OperationStatus.SUCCESS

        return SaveTasksPayload(
            status=status,
            tasks=result.successful,
            errors=errors,
        )

    @validate_arguments
    async def complete(self, info, input: CompleteTasksInput):
        try:
            result = await rexflow.complete_tasks(input.tasks)
        except REXFlowError as e:
            return SaveTasksPayload(
                status=OperationStatus.FAILURE,
                errors=[GenericProblem(message=e)],
            )

        errors = []
        for error in result.errors:
            if isinstance(error, ValidationErrorDetails):
                for dataId, validation_error in error.errors.items():
                    errors.append(ValidationProblem(
                        message=validation_error['message'],
                        iid=error.iid,
                        tid=error.tid,
                        dataId=dataId,
                        validator=validation_error['validator'],
                    ))
            else:
                errors.append(GenericProblem(str(error)))

        if errors:
            status = OperationStatus.FAILURE
        else:
            status = OperationStatus.SUCCESS

        return CompleteTaskPayload(
            status=status,
            tasks=result.successful,
            errors=errors
        )


class WorkflowMutations:
    def __init__(self, *_) -> None:
        pass

    @validate_arguments
    async def start(self, info, input: StartWorkflowInput):
        logger.info(input)
        try:
            workflow = await rexflow.start_workflow(input.did)
        except BridgeNotReachableError:
            logger.exception('Could not reach rexflow bridge')
            return StartWorkflowPayload(
                status=OperationStatus.FAILURE,
                errors=[ServiceNotAvailableProblem(
                    message='Could not reach rexflow bridge',
                )]
            )

        return StartWorkflowPayload(
            status=OperationStatus.SUCCESS,
            iid=workflow.iid,
            workflow=workflow,
        )

    async def tasks(self, info):
        return TasksMutations()


mutation.set_field('workflow', WorkflowMutations)


class TalkTrackMutations:
    def __init__(self, *_):
        pass

    @validate_arguments
    async def start(self, info, input: StartTalkTrackInput):
        request = info.context['request']
        session_id = request.headers.get(settings.SESSION_ID_HEADER, 'anon')

        async_tasks = []
        for talktrack_id in input.talktrack_id:
            async_task = talktrack_actions.start_talktrack(
                session_id,
                talktrack_id,
            )
            async_tasks.append(async_task)

        talktracks = await asyncio.gather(*async_tasks)

        return StartTalkTrackPayload(
            status=OperationStatus.SUCCESS,
            talktracks=talktracks,
        )

    @validate_arguments
    async def activate(self, info, input: ActivateTalkTrackInput):
        request = info.context['request']
        session_id = request.headers.get(settings.SESSION_ID_HEADER, 'anon')

        talktrack = await talktrack_actions.activate_talktrack(
            session_id,
            input.talktrack_uuid,
        )

        return ActivateTalkTrackPayload(
            status=OperationStatus.SUCCESS,
            talktrack=talktrack,
        )

    @validate_arguments
    async def finish(self, info, input: FinishTalkTrackInput):
        request = info.context['request']
        session_id = request.headers.get(settings.SESSION_ID_HEADER, 'anon')

        for talktrack_uuid in input.talktrack_uuid:
            talktrack_actions.finish_talktrack(session_id, talktrack_uuid)

        return FinishTalkTrackPayload(
            status=OperationStatus.SUCCESS,
        )


mutation.set_field('talktrack', TalkTrackMutations)
