import logging

from pydantic import validate_arguments

from .entities import (
    CompleteWorkflowInput,
    CompleteWorkflowPayload,
    Problem,
    StartTaskInput,
    StartTaskPayload,
)
from rexflow_ui import api
from rexflow_ui.errors import BridgeNotReachableError
from rexflow_ui.entities.types import (
    OperationStatus,
)


logger = logging.getLogger(__name__)


def query_health(*_):
    return 'OK'


class TaskMutations:
    def __init__(self, *_) -> None:
        pass

    @validate_arguments
    async def start(self, info, input: StartTaskInput):
        try:
            logger.info(
                f'Starting task {input.tid} for instance {input.iid}'
            )
            await api.start_tasks(input.iid, [input.tid])
        except BridgeNotReachableError:
            logger.exception('Could not reach rexflow bridge')
            return StartTaskPayload(
                status=OperationStatus.FAILURE,
                errors=[
                    Problem(
                        message='Trying to connect to an unreachable bridge',
                    )
                ]
            )
        except Exception as ex:
            logger.exception('Error when starting task')
            return StartTaskPayload(
                status=OperationStatus.FAILURE,
                errors=[
                    Problem(message=str(ex))
                ]
            )

        return StartTaskPayload(
            status=OperationStatus.SUCCESS,
        )


class WorkflowMutations:
    def __init__(self, *_) -> None:
        pass

    @validate_arguments
    async def complete(self, info, input: CompleteWorkflowInput):
        try:
            logger.info(f'Complete workflow {input.iid}')
            await api.complete_workflow(input.iid)
        except Exception as ex:
            logger.exception('Error when completing workflow')
            return CompleteWorkflowPayload(
                status=OperationStatus.FAILURE,
                errors=[
                    Problem(message=str(ex))
                ]
            )

        return CompleteWorkflowPayload(
            status=OperationStatus.SUCCESS,
        )
