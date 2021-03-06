import logging
from functools import wraps

from graphql.type.definition import GraphQLResolveInfo
from jose.exceptions import JWTError
from pydantic.error_wrappers import ValidationError

from .errors import HttpUnauthorizedError
from prism_api import settings
from prism_api.okta.actions import (
    get_access_token,
    validate_access_token,
)

logger = logging.getLogger(__name__)


async def _verify_access_token(info: GraphQLResolveInfo):
    if settings.DISABLE_AUTHENTICATION:
        info.context['access_token'] = None
        info.context['session_id'] = 'anon'
        return

    access_token = get_access_token(info.context['request'])

    if access_token is None:
        raise HttpUnauthorizedError('Missing access token')

    try:
        token = await validate_access_token(access_token)
    except ValidationError as e:
        logger.exception('Wrong token format')
        raise HttpUnauthorizedError from e
    except JWTError as e:
        logger.exception('Invalid Token')
        raise HttpUnauthorizedError from e

    info.context['access_token'] = token
    info.context['session_id'] = token.sub


def resolver_verify_token(f):
    @wraps(f)
    async def _requires_token(obj, info: GraphQLResolveInfo, *args, **kwargs):
        await _verify_access_token(info)
        return await f(obj, info, *args, **kwargs)
    return _requires_token
