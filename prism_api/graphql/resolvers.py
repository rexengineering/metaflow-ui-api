import logging
from typing import List, Optional

from graphql.type.definition import GraphQLResolveInfo
from pydantic.decorator import validate_arguments


from .decorators import resolver_verify_token
from .entities.wrappers import (
    CancelWorkflowInput,
    CancelWorkflowPayload,
    CompleteTaskPayload,
    CompleteTasksInput,
    GenericProblem,
    Problem,
    SaveTaskInput,
    SaveTasksPayload,
    StartWorkflowByNameInput,
    StartWorkflowByNamePayload,
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
from rexflow_ui import api as rexflow
from rexflow_ui.errors import (
    BridgeNotReachableError,
    REXFlowError,
    ValidationErrorDetails,
)
from rexflow_ui.entities.types import (
    MetaData,
    OperationStatus,
    Workflow,
    WorkflowDeployment,
)
from prism_api.state_manager import store
from prism_api.state_manager.entities import Session

logger = logging.getLogger(__name__)


# Problem resolvers

def resolve_problem_interface_type(obj: Problem, *_):
    return obj.resolve_type()


# Query resolvers

@resolver_verify_token
async def resolve_session(_, info: GraphQLResolveInfo):
    session_id = info.context['session_id']
    state = await store.read_raw_state(session_id)
    return Session(
        id=session_id,
        state=state,
    )


class WorkflowResolver:
    def __init__(self, *_):  # pragma: no cover
        pass

    @resolver_verify_token
    @validate_arguments
    async def active(
        self,
        info,
        filter: WorkflowFilter = None
    ):
        session_id = info.context['session_id']
        iids = [] if filter is None else filter.ids
        workflows = await rexflow.get_active_workflows(
            iids,
            metadata={
                'session_id': session_id,
            },
        )
        return workflows

    @resolver_verify_token
    async def available(self, *_):
        available_workflows = await rexflow.get_available_workflows(
            refresh=True
        )
        return available_workflows

    @resolver_verify_token
    async def deployments(self, *_):
        available_workflows = await rexflow.get_available_workflows(
            refresh=True
        )
        deployments = []
        for workflow in available_workflows:
            if workflow.deployments:
                deployments.extend(workflow.deployments)

        return deployments

    @resolver_verify_token
    async def directory(self, *_):
        available_workflows = await rexflow.get_available_workflows(
            refresh=True
        )

        workflow_directory = {}
        for workflow in available_workflows:
            if workflow.deployments:
                deployment = workflow.deployments.pop()
                workflow_directory[workflow.name] = deployment

        return workflow_directory


@resolver_verify_token
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


class TalkTrackResolver:
    def __init__(self, *_):  # pragma: no cover
        pass

    async def list(self, *_) -> List[WorkflowDeployment]:
        workflows = await rexflow.get_available_workflows(refresh=True)
        talktracks = [
            deployment
            for deployment in workflows
            if deployment.name in settings.TALKTRACK_WORKFLOWS
        ]
        return talktracks


# Mutation resolvers

class StateMutations:
    @resolver_verify_token
    @validate_arguments
    async def update(self, info, input: UpdateStateInput):
        session_id = info.context['session_id']
        state = await store.save_raw_state(session_id, input.state)
        return UpdateStatePayload(
            status=OperationStatus.SUCCESS,
            state=state,
        )


class SessionMutations:
    def __init__(sel, *_) -> None:  # pragma: no cover
        pass

    @resolver_verify_token
    async def start(self, info: GraphQLResolveInfo):
        session_id = info.context['session_id']
        return {
            'status': OperationStatus.SUCCESS,
            'session': {
                'id': session_id,
                'state': '',
            },
        }

    @resolver_verify_token
    async def state(self, _):
        return StateMutations()

    @resolver_verify_token
    async def close(self, _):
        return {
            'status': OperationStatus.SUCCESS,
        }


class TasksMutations:

    @resolver_verify_token
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
                errors.append(GenericProblem(message=error.message))

        if errors:
            status = OperationStatus.FAILURE
        else:
            status = OperationStatus.SUCCESS

        return ValidateTasksPayload(
            status=status,
            tasks=result.successful,
            errors=errors
        )

    @resolver_verify_token
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
                errors.append(GenericProblem(message=error.message))

        if errors:
            status = OperationStatus.FAILURE
        else:
            status = OperationStatus.SUCCESS

        return SaveTasksPayload(
            status=status,
            tasks=result.successful,
            errors=errors,
        )

    @resolver_verify_token
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
                errors.append(GenericProblem(message=error.message))

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

    @resolver_verify_token
    @validate_arguments
    async def start(self, info, input: StartWorkflowInput):
        logger.info(input)
        metadata = []

        session_id = info.context['session_id']
        metadata.append(MetaData(key='session_id', value=session_id))

        deployment = await rexflow.find_workflow_deployment(input.did)
        if deployment.name in settings.TALKTRACK_WORKFLOWS:
            metadata.append(MetaData(
                key='type',
                value='talktrack',
            ))

        try:
            workflow = await rexflow.start_workflow(
                input.did,
                metadata=metadata,
            )
        except BridgeNotReachableError:
            logger.exception('Could not reach rexflow bridge')
            return StartWorkflowPayload(
                status=OperationStatus.FAILURE,
                errors=[ServiceNotAvailableProblem(
                    message='Could not reach rexflow bridge',
                )]
            )
        except REXFlowError as e:
            logger.exception('Error when communicating with REXFlow')
            return StartWorkflowPayload(
                status=OperationStatus.FAILURE,
                errors=[GenericProblem(
                    message=str(e),
                )]
            )

        return StartWorkflowPayload(
            status=OperationStatus.SUCCESS,
            iid=workflow.iid,
            workflow=workflow,
        )

    @resolver_verify_token
    @validate_arguments
    async def start_by_name(self, info, input: StartWorkflowByNameInput):
        logger.info(input)
        metadata = []

        session_id = info.context['session_id']
        metadata.append(MetaData(key='session_id', value=session_id))

        if input.name in settings.TALKTRACK_WORKFLOWS:
            metadata.append(MetaData(
                key='type',
                value='talktrack',
            ))

        try:
            workflow = await rexflow.start_workflow_by_name(
                workflow_name=input.name,
                metadata=metadata,
            )
        except BridgeNotReachableError:
            logger.exception('Could not reach rexflow bridge')
            return StartWorkflowByNamePayload(
                status=OperationStatus.FAILURE,
                errors=[ServiceNotAvailableProblem(
                    message='Could not reach rexflow bridge',
                )]
            )
        except REXFlowError:
            logger.exception(f'Workflow {input.name} is not deployed')
            return StartWorkflowByNamePayload(
                status=OperationStatus.FAILURE,
                errors=[ServiceNotAvailableProblem(
                    message=f'Workflow {input.name} is not deployed',
                )]
            )

        return StartWorkflowByNamePayload(
            status=OperationStatus.SUCCESS,
            did=workflow.did,
            iid=workflow.iid,
            workflow=workflow,
        )

    @resolver_verify_token
    @validate_arguments
    async def cancel(self, info, input: CancelWorkflowInput):
        logger.info('Canceling workflows:')
        logger.info(input.iid)

        successful_iids = []
        errors = []
        for iid in input.iid:
            success = await rexflow.cancel_workflow(iid)
            if success:
                successful_iids.append(iid)
            else:
                errors.append(GenericProblem(
                    message=f'Failed to cancel workflow {iid}'
                ))
        status = OperationStatus.FAILURE if errors else OperationStatus.SUCCESS

        return CancelWorkflowPayload(
            status=status,
            iid=successful_iids,
            errors=errors,
        )

    async def tasks(self, info):
        return TasksMutations()
