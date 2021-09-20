import asyncio
from datetime import datetime, timedelta

from .decorators import _verify_access_token, resolver_verify_token
from prism_api.events import Event, EventManager, EventWrapper


class Subscription:
    keep_alive = None


async def event_generator(obj, info):
    await _verify_access_token(info)
    session_id = info.context['session_id']
    events = EventManager.get_manager(session_id)
    events.start_listening()

    Subscription.keep_alive = datetime.now() + timedelta(seconds=60)
    yield EventWrapper(event=Event.START_BROADCAST)

    while Subscription.keep_alive > datetime.now():
        try:
            yield await events.get()
        except asyncio.TimeoutError:
            pass

    events.stop_listening()
    yield EventWrapper(event=Event.FINISH_BROADCAST)


async def broadcast_event_subscription(event: EventWrapper, info):
    if event:
        return {
            'status': 'Active',
            'event': event.event,
            'data': event.data,
        }

    return {'status': 'Error'}


@resolver_verify_token
async def trigger_event_mutation(_, info):
    session_id = info.context['session_id']
    events = EventManager.get_manager(session_id)
    await events.dispatch(Event.START_WORKFLOW)
    return {'status': 'Ok'}


async def keep_alive_subscription_mutation(_, info):
    Subscription.keep_alive = datetime.now() + timedelta(seconds=60)
    return {'status': 'Ok'}
