from starlette.requests import Request

from .workflows import (
    cancel_workflow,
    get_workflow_instances,
    start_workflow,
)


async def resolve_version(*_):
    return '0.0.0.mock'


def _get_did(info):
    request: Request = info.context['request']
    return request.query_params.get('did')


async def resolve_get_instances(_, info):
    did = _get_did(info)
    return await get_workflow_instances(did)


async def resolve_create_instance(_, info, input):
    did = _get_did(info)
    callback = input['graphqlUri']
    iid = await start_workflow(did, callback)
    return {
        'did': did,
        'iid': iid,
        'status': 'SUCCESS' if iid else 'FAILURE',
        'tasks': [],
    }


async def resolve_cancel_instance(_, info, input):
    did = _get_did(info)
    iid = input['iid']
    await cancel_workflow(did, iid)
    return {
        'did': did,
        'iid': iid,
        'iid_status': 'ERROR',
        'status': 'SUCCESS',
    }
