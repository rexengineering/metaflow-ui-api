import logging

from ariadne import QueryType, MutationType
from pydantic import validate_arguments

from . import entities as w
from prism_api.rexflow import api
from prism_api.rexflow.entities import types as e


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
    async def start(self, info, input: w.StartTaskInput):
        try:
            await api.start_tasks(input.iid, [input.tid])
        except Exception as ex:
            logger.exception('Error when starting task')
            return w.StartTaskPayload(
                status=e.OperationStatus.FAILURE,
                errors=[
                    w.Problem(message=str(ex))
                ]
            )

        return w.StartTaskPayload(
            status=e.OperationStatus.SUCCESS,
        )


mutation.set_field('task', Task)


class Workflow:
    def __init__(self, *_) -> None:
        pass

    @validate_arguments
    async def complete(self, info, input: w.CompleteWorkflowInput):
        try:
            await api.complete_workflow(input.iid)
        except Exception as ex:
            logger.exception('Error when completing workflow')
            return w.CompleteWorkflowPayload(
                status=e.OperationStatus.FAILURE,
                errors=[
                    w.Problem(message=str(ex))
                ]
            )

        return w.CompleteWorkflowPayload(
            status=e.OperationStatus.SUCCESS,
        )


mutation.set_field('workflow', Workflow)
