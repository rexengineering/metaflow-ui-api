import asyncio

from .decorators import resolver_verify_token
from prism_api.rexflow import api as rexflow


async def counter_generator(_, info):
    for i in range(5):
        await asyncio.sleep(1)
        yield i


@resolver_verify_token
async def active_workflows_subscription(count, info):
    session_id = info.context['session_id']
    workflows = await rexflow.get_active_workflows(
        session_id=session_id,
        iids=[],
    )
    return workflows
