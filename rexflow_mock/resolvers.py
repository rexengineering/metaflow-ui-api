from starlette.requests import Request

from .workflows import (
    get_workflow_instances,
)


async def resolve_version(*_):
    return '0.0.0.mock'


async def resolve_get_instances(_, info):
    request: Request = info.context['request']
    did = request.query_params.get('did')
    return await get_workflow_instances(did)
