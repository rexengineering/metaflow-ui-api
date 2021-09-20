from __future__ import annotations
import asyncio

from .entities import Event, EventWrapper
from prism_api.state_manager.entities import SessionId


class NotListeningError(Exception):
    """Trying to get events from a manager that is not listening"""


class EventManager:
    managers: dict[SessionId, EventManager] = {}

    @classmethod
    def get_manager(cls, session_id: SessionId) -> EventManager:
        if session_id not in cls.managers:
            cls.managers[session_id] = cls(session_id=session_id)

        return cls.managers[session_id]

    def __init__(self, session_id: SessionId):
        self.event_queue: asyncio.Queue = None
        self.session_id: SessionId = session_id
        self.listeners = []

    def start_listening(self, listener='singleton'):
        if self.listeners == []:
            self.event_queue = asyncio.Queue()
        self.listeners.append(listener)

    def stop_listening(self, listener='singleton'):
        self.listeners.remove(listener)
        if self.listeners == []:
            self.event_queue = None

    async def dispatch(self, event: Event, data: dict = {}):
        if self.listeners:
            wrapper = EventWrapper(
                event=event,
                data=data,
            )
            await self.event_queue.put(wrapper)

    async def get(self, timeout=60) -> EventWrapper:
        if not self.listeners:
            raise NotListeningError

        return await asyncio.wait_for(
            self.event_queue.get(),
            timeout=timeout,
        )
