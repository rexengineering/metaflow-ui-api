import abc

from rexredis import RexRedis


class StoreABC(abc.ABC):
    def __init__(self, client_id: str):
        self.client_id = client_id

    async def read(self) -> str:
        raise NotImplementedError

    async def save(self, state: str) -> str:
        raise NotImplementedError


class RedisStore(StoreABC):
    _redis = None

    @classmethod
    def _get_redis(cls):
        if cls._redis is None or cls._redis.ping() is False:
            cls._redis = RexRedis()
        return cls._redis

    def __init__(self, client_id: str):
        super().__init__(client_id)
        self.redis = self._get_redis()

    async def read(self) -> str:
        return self.redis.get_val(self.client_id) or '{}'

    async def save(self, state: str) -> str:
        self.redis.set_val(self.client_id, state)
        return await self.read()
