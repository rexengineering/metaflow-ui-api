import logging
from typing import Union

from httpx import AsyncClient, ConnectError
from jose import jwk, jwt
from starlette.requests import Request

from .settings import (
    BASE_URI,
    CLIENT_ID,
    AUTHORIZATION_HEADER,
    ID_TOKEN_HEADER,
    AUDIENCE,
)
from .entities import (
    Token,
    JWKSResponse,
    TokenHeader,
)
from .errors import OktaError


logger = logging.getLogger(__name__)


def get_access_token(request: Request) -> Union[str, None]:
    access_token = request.headers.get(AUTHORIZATION_HEADER)
    return access_token


def get_id_token(request: Request) -> Union[str, None]:
    id_token = request.headers.get(ID_TOKEN_HEADER)
    return id_token


async def validate_access_token(access_token: str) -> Token:
    headers = TokenHeader(**jwt.get_unverified_header(access_token))
    keys = await get_json_web_keys()
    key = jwk.construct(keys[headers.kid].dict())
    decoded = jwt.decode(
        access_token,
        key,
        algorithms=[headers.alg],
        audience=AUDIENCE,
    )
    token = Token(**decoded)
    return token


async def validate_id_token(id_token: str, access_token: str):
    headers = TokenHeader(**jwt.get_unverified_header(id_token))
    keys = await get_json_web_keys()
    key = jwk.construct(keys[headers.kid].dict())
    decoded = jwt.decode(
        id_token,
        key,
        algorithms=[headers.alg],
        audience=CLIENT_ID,
        access_token=access_token,
    )
    return decoded  # TODO Add a entity for decoded id token


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
