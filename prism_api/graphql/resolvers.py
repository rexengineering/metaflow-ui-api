import logging

from ariadne import QueryType, MutationType

from prism_api.rexflow import entities as rxen

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
        filter: rxen.WorkflowFilter = None
    ):
        return [
            rxen.Workflow(
                iid='test',
                status=rxen.WorkflowStatus.IN_PROGRESS,
            )
        ]

    async def available(self, *_):
        return [
            '123',
            '456',
        ]


query.set_field('workflows', WorkflowResolver)


mutation = MutationType()


class StateMutations:
    async def update(*_, input):
        return {
            'status': rxen.OperationStatus.SUCCESS,
            'state': ''
        }


class SessionMutations:
    def __init__(sel, *_) -> None:
        pass

    async def start(self, _):
        return {
            'status': rxen.OperationStatus.SUCCESS,
            'session': {
                'id': '',
                'state': '',
            },
        }

    async def state(self, _):
        return StateMutations()

    async def close(self, _):
        return {
            'status': rxen.OperationStatus.SUCCESS,
        }


mutation.set_field('session', SessionMutations)


class TasksMutations:
    async def start(self, info, input: rxen.StartTasksInput):
        return rxen.StartTasksPayload(
            status=rxen.OperationStatus.SUCCESS,
            tasks=[
                rxen.Task(
                    id='123',
                    status=rxen.TaskStatus.IN_PROGRESS,
                )
            ]
        )

    async def validate(self, info, input: rxen.ValidateTaskInput):
        return rxen.ValidateTasksPayload(
            status=rxen.OperationStatus.SUCCESS,
            tasks=[
                rxen.Task(
                    id='123',
                    status=rxen.TaskStatus.IN_PROGRESS,
                )
            ]
        )

    async def save(self, info, input: rxen.SaveTaskInput):
        return rxen.SaveTasksPayload(
            status=rxen.OperationStatus.SUCCESS,
            tasks=[
                rxen.Task(
                    id='123',
                    status=rxen.TaskStatus.IN_PROGRESS,
                )
            ]
        )

    async def complete(self, info, input: rxen.CompleteTasksInput):
        return rxen.CompleteTaskPayload(
            status=rxen.OperationStatus.SUCCESS,
            tasks=[
                rxen.Task(
                    id='123',
                    status=rxen.TaskStatus.FINISHED,
                )
            ]
        )


class WorkflowMutations:
    def __init__(self, *_) -> None:
        pass

    async def start(self, info, input: rxen.StartWorkflowInput):
        logger.info(input)
        return rxen.StartWorkflowPayload(
            status=rxen.OperationStatus.SUCCESS,
            iid='123',
        )

    async def complete(self, info, input: rxen.CompleteWorkflowInput):
        logger.info(input)
        return rxen.CompleteWorkflowPayload(
            status=rxen.OperationStatus.SUCCESS,
            iid='123'
        )

    async def tasks(self, info):
        return TasksMutations()


mutation.set_field('workflow', WorkflowMutations)
