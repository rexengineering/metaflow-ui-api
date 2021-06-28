import logging
from functools import wraps

from ariadne.exceptions import HttpError
from graphql.type.definition import GraphQLResolveInfo
from jose.exceptions import JWTError
from pydantic.error_wrappers import ValidationError

from .actions import get_access_token, validate_access_token


logger = logging.getLogger(__name__)


class HttpUnauthorizedError(HttpError):
    status = '401 Unauthorized'


def resolver_verify_token(f):
    @wraps(f)
    async def _requires_token(obj, info: GraphQLResolveInfo, *args, **kwargs):
        access_token = get_access_token(info.context['request'])

        if access_token is None:
            raise HttpUnauthorizedError('Missing access token')

        try:
            token = await validate_access_token(access_token)
        except ValidationError as e:
            print('Wrong token format')
            raise HttpUnauthorizedError from e
        except JWTError as e:
            logger.error('Invalid Token')
            raise HttpUnauthorizedError from e

        info.context['access_token'] = token
        info.context['session_id'] = token.sub

        return await f(obj, info, *args, **kwargs)
    return _requires_token
