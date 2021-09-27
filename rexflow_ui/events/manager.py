from __future__ import annotations
import asyncio
import logging

from .entities import Event, EventWrapper
from prism_api.state_manager.entities import SessionId

logger = logging.getLogger(__name__)


class NotListeningError(Exception):
    """Trying to get events from a manager that is not listening"""


class EventManager:
    managers: dict[SessionId, EventManager] = {}

    @classmethod
    def get_manager(cls, listener='singleton') -> EventManager:
        if listener not in cls.managers:
            raise NotListeningError

        return cls.managers[listener]

    @classmethod
    def start_listening(cls, listener='singleton') -> EventManager:
        if listener not in cls.managers:
            cls.managers[listener] = cls()

        return cls.managers[listener]

    @classmethod
    def stop_listening(cls, listener='singleton'):
        del cls.managers[listener]

    @classmethod
    def dispatch(cls, event: Event, data: dict = {}):
        for manager in cls.managers.values():
            wrapper = EventWrapper(
                event=event,
                data=data,
            )
            try:
                manager.event_queue.put_nowait(wrapper)
            except asyncio.queues.QueueFull:
                logger.exception(f'Could not put an event in queue: {event}')

    def __init__(self):
        self.event_queue: asyncio.Queue = asyncio.Queue()

    async def get(self, timeout=60) -> EventWrapper:
        return await asyncio.wait_for(
            self.event_queue.get(),
            timeout=timeout,
        )
