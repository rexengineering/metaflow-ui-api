from __future__ import annotations
import asyncio
import json
import logging

from rexredis import RexRedis

from .base import EventManager as BaseEventManager
from ..entities import Event, EventWrapper
from ..errors import NotListeningError

logger = logging.getLogger(__name__)


class EventManager(BaseEventManager):
    _redis = None

    _listeners: dict[str, EventManager] = {}

    LISTENER_CHANNEL = 'rexflow-events'

    @classmethod
    def get_manager(cls, listener='singleton') -> EventManager:
        if listener not in cls._listeners:
            raise NotListeningError
        return cls._listeners[listener]

    @classmethod
    def start_listening(cls, listener='singleton') -> EventManager:
        if listener not in cls._listeners:
            cls._listeners[listener] = cls(listener)
        return cls._listeners[listener]

    @classmethod
    def stop_listening(cls, listener='singleton'):
        del cls._listeners[listener]

    @classmethod
    def dispatch(cls, event: Event, data: dict = {}):
        wrapper = EventWrapper(
            event=event,
            data=data,
        )
        logger.info(f'Dispatching {event} to Redis')
        redis = cls._get_redis()
        redis._conn.publish(cls.LISTENER_CHANNEL, wrapper.json())

    @classmethod
    def _get_redis(cls):
        if cls._redis is None or cls._redis.ping() is False:
            cls._redis = RexRedis()
        return cls._redis

    def __init__(self, listener_key: str):
        super().__init__()
        self._redis = self._get_redis()
        self._listener_key = listener_key
        self._subscription = self._redis._conn.pubsub()
        self._subscription.subscribe(self.LISTENER_CHANNEL)

    def __del__(self):
        self._subscription.unsubscribe(self.LISTENER_CHANNEL)

    async def get(self, timeout=60) -> EventWrapper:
        return await asyncio.wait_for(
            self._get_message(),
            timeout=timeout,
        )

    async def _get_message(self) -> EventWrapper:
        while True:
            message = self._subscription.get_message(
                ignore_subscribe_messages=True,
            )
            if message:
                data = json.loads(message['data'])
                return EventWrapper(**data)
            await asyncio.sleep(1)
