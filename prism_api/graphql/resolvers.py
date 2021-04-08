from ariadne import QueryType, ObjectType

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
