from typing import Union

from rexredis import RexRedis

from .entities import JWKSResponse
from .settings import JWKS_EXPIRATION_SEC

JWKS_KEY = 'okta:jwks'


class Store:
    _redis = None

    @classmethod
    def _get_redis(cls):  # pragma: no cover
        if cls._redis is None or cls._redis.ping() is False:
            cls._redis = RexRedis()
        return cls._redis

    @classmethod
    def save_jwks(cls, jwks: JWKSResponse):  # pragma: no cover
        redis = cls._get_redis()
        redis.set_val(
            JWKS_KEY,
            jwks.json(),
            ex=JWKS_EXPIRATION_SEC,
        )

    @classmethod
    def get_jwks(cls) -> Union[JWKSResponse, None]:  # pragma: no cover
        redis = cls._get_redis()
        data = redis.get_from_json(JWKS_KEY)
        if data:
            jwks = JWKSResponse(**data)
            return jwks
        else:
            return None
