import logging

import jwt
from httpx import AsyncClient, ConnectError
from pydantic import validate_arguments

from .settings import (
    BASE_URI,
    CLIENT_ID,
)
from .entities import (
    Token,
    JWKSResponse,
    TokenHeader,
    TokenWrapper,
)
from .errors import OktaError


logger = logging.getLogger(__name__)


@validate_arguments
async def validate_access_token(wrapper: TokenWrapper):
    headers = TokenHeader(**jwt.get_unverified_header(wrapper.access_token))
    keys = await get_json_web_keys()
    key = keys[headers.kid]
    decoded = jwt.decode(wrapper.access_token, key.n, algorithms=[headers.alg])
    token = Token(**decoded)
    return token


async def get_json_web_keys():
    endpoint = f'{BASE_URI}/v1/keys?client_id={CLIENT_ID}'
    async with AsyncClient() as client:
        try:
            result = await client.get(endpoint)
        except ConnectError as e:
            logger.exception('Could not connect to Okta')
            raise OktaError from e
    response = JWKSResponse(**result.json())
    return {key.kid: key for key in response.keys}


def request_id_token():
    ...


def request_access_token():
    ...


def request_user_info():
    ...
