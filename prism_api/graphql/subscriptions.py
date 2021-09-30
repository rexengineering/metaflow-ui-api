import asyncio
import logging
from datetime import datetime, timedelta

from .decorators import _verify_access_token
from .entities.wrappers import EventBroadcastPayload, KeepAlivePayload
from rexflow_ui.events import Event, EventManager, EventWrapper
from rexflow_ui.entities.types import OperationStatus

logger = logging.getLogger(__name__)


class Subscription:
    keep_alive = None


async def event_generator(obj, info):
    await _verify_access_token(info)
    session_id = info.context['session_id']
    events = EventManager.start_listening(listener=session_id)

    Subscription.keep_alive = datetime.now() + timedelta(seconds=60)
    yield EventWrapper(event=Event.START_BROADCAST)

    while Subscription.keep_alive > datetime.now():
        try:
            event = await events.get()
        except asyncio.TimeoutError:
            pass
        else:
            workflow: dict = event.data.get('workflow')
            if workflow is None:
                yield event
            if workflow.get('metadata_dict', {}).get('session_id') == session_id:  # noqa E501
                yield event

    EventManager.stop_listening(session_id)
    yield EventWrapper(event=Event.FINISH_BROADCAST)


async def broadcast_event_subscription(event: EventWrapper, info):
    if event:
        return EventBroadcastPayload(
            event=event.event,
            data=event.data,
        )

    logger.error('Unexpected event broadcast termination')
    return EventBroadcastPayload(event=Event.ERROR_BROADCAST)


async def keep_alive_subscription_mutation(_, info):
    Subscription.keep_alive = datetime.now() + timedelta(seconds=60)
    return KeepAlivePayload(status=OperationStatus.SUCCESS)
