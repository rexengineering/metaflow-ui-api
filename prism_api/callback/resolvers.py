from ariadne import QueryType, MutationType
from pydantic import validate_arguments

from . import entities as w
from prism_api.rexflow.entities import types as e


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
        return w.StartTaskPayload(
            status=e.OperationStatus.SUCCESS,
        )


mutation.set_field('task', Task)


class Workflow:
    def __init__(self, *_) -> None:
        pass

    @validate_arguments
    async def complete(self, info, input: w.CompleteWorkflowInput):
        return w.CompleteWorkflowPayload(
            status=e.OperationStatus.SUCCESS,
        )


mutation.set_field('workflow', Workflow)
