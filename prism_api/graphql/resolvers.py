from ariadne import QueryType, ObjectType, MutationType

from prism_api.rexflow import entities as rxen


query = QueryType()


@query.field('session')
async def resolve_session(*_):
    # TODO add model for Session
    return {
        'id': '',
        'state': '',
    }


@query.field('workflows')
async def resolve_workflows(*_):
    return {}


workflow_query = ObjectType('WorkflowQuery')


@workflow_query.field('active')
async def resolve_workflow_active(obj, *_, filter: rxen.WorkflowFilter = None):
    return [
        rxen.Workflow(
            iid='test',
            status=rxen.WorkflowStatus.IN_PROGRESS,
        )
    ]


@workflow_query.field('available')
async def resolve_workflow_available(obj, *_):
    return [
        '123',
        '456',
    ]


mutation = MutationType()


@mutation.field('session')
async def resolve_session_mutation(*_):
    return {}


session_mutations = ObjectType('SessionMutations')


@session_mutations.field('start')
async def resolve_session_start(*_):
    return {
        'status': rxen.OperationStatus.SUCCESS,
        'session': {
            'id': '',
            'state': '',
        },
    }


@session_mutations.field('state')
async def resolve_session_state(*_):
    return {}


state_mutations = ObjectType('StateMutations')


@state_mutations.field('update')
async def resolve_session_state_update(*_, input):
    return {
        'status': rxen.OperationStatus.SUCCESS,
        'state': ''
    }


@session_mutations.field('close')
async def resolve_session_close(*_):
    return {
        'status': rxen.OperationStatus.SUCCESS,
    }
