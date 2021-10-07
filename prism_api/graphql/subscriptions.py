import asyncio
import logging
from datetime import datetime, timedelta

from .decorators import _verify_access_token, resolver_verify_token
from .entities.wrappers import (
    EventBroadcastPayload,
    EventData,
    KeepAlivePayload,
)
from rexflow_ui.events import Event, EventManager, EventWrapper
from rexflow_ui.entities.types import OperationStatus

logger = logging.getLogger(__name__)


class Subscription:
    expiration_time = None

    @classmethod
    def keep_alive(cls):
        cls.expiration_time = datetime.now() + timedelta(seconds=60)


async def event_generator(obj, info):
    await _verify_access_token(info)
    session_id = info.context['session_id']
    events = EventManager.start_listening(listener=session_id)

    Subscription.keep_alive()
    yield EventWrapper(event=Event.START_BROADCAST)

    while Subscription.expiration_time > datetime.now():
        try:
            event = await events.get()
        except asyncio.TimeoutError:
            pass
        else:
            if event.event == Event.KEEP_ALIVE:
                if event.data.get('session_id') == session_id:
                    Subscription.keep_alive()
            else:
                workflow: dict = event.data.get('workflow')
                if workflow is None or workflow.get(
                    'metadata_dict',
                    {},
                ).get('session_id') == session_id:
                    yield event

    EventManager.stop_listening(session_id)
    yield EventWrapper(event=Event.FINISH_BROADCAST)


async def broadcast_event_subscription(event: EventWrapper, info):
    if event:
        return EventBroadcastPayload(
            event=event.event,
            data=EventData(**event.data),
        )

    logger.error('Unexpected event broadcast termination')
    return EventBroadcastPayload(event=Event.ERROR_BROADCAST)


@resolver_verify_token
async def keep_alive_subscription_mutation(_, info):
    session_id = info.context['session_id']
    EventManager.dispatch(Event.KEEP_ALIVE, data={'session_id': session_id})
    return KeepAlivePayload(status=OperationStatus.SUCCESS)
