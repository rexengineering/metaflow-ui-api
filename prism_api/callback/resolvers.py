import logging

from ariadne import QueryType, MutationType
from pydantic import validate_arguments

from .entities import (
    CompleteWorkflowInput,
    CompleteWorkflowPayload,
    Problem,
    StartTaskInput,
    StartTaskPayload,
)
from prism_api.rexflow import api
from prism_api.rexflow.entities.types import (
    OperationStatus,
)


logger = logging.getLogger(__name__)

query = QueryType()


@query.field('health')
def query_health(*_):
    return 'OK'


mutation = MutationType()


class Task:
    def __init__(self, *_) -> None:
        pass

    @validate_arguments
    async def start(self, info, input: StartTaskInput):
        try:
            logger.info(
                f'Starting task {input.tid} for instance {input.iid}'
            )
            await api.start_tasks(input.iid, [input.tid])
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


mutation.set_field('task', Task)


class Workflow:
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


mutation.set_field('workflow', Workflow)
