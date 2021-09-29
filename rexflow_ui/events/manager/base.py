from __future__ import annotations
import abc

from ..entities import Event, EventWrapper


class EventManager(abc.ABC):
    @classmethod
    @abc.abstractmethod
    def get_manager(cls, listener='singleton') -> EventManager:
        raise NotImplementedError

    @classmethod
    @abc.abstractmethod
    def start_listening(cls, listener='singleton') -> EventManager:
        raise NotImplementedError

    @classmethod
    @abc.abstractmethod
    def stop_listening(cls, listener='singleton'):
        raise NotImplementedError

    @classmethod
    @abc.abstractmethod
    def dispatch(cls, event: Event, data: dict = {}):
        raise NotImplementedError

    @abc.abstractmethod
    async def get(self, timeout=60) -> EventWrapper:
        raise NotImplementedError
