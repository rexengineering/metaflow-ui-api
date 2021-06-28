import logging
from functools import wraps

from graphql.type.definition import GraphQLResolveInfo

from .validators import verify_access_token

logger = logging.getLogger(__name__)


def resolver_verify_token(f):
    @wraps(f)
    async def _requires_token(obj, info: GraphQLResolveInfo, *args, **kwargs):
        await verify_access_token(info)
        return await f(obj, info, *args, **kwargs)
    return _requires_token
