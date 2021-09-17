import asyncio
from datetime import datetime, timedelta
from enum import Enum

from .decorators import _verify_access_token


class Subscription:
    keep_alive = None


class Event(str, Enum):
    START_WORKFLOW = 'START_WORKFLOW'
    UPDATE_WORKFLOW = 'UPDATE_WORKFLOW'
    FINISH_WORKFLOW = 'FINISH_WORKFLOW'


event_queue: asyncio.Queue = asyncio.Queue()


async def event_generator(obj, info):
    await _verify_access_token(info)
    Subscription.keep_alive = datetime.now() + timedelta(seconds=60)
    while Subscription.keep_alive > datetime.now():
        try:
            yield await asyncio.wait_for(event_queue.get(), 60)
        except asyncio.TimeoutError:
            pass

    yield None


async def broadcast_event_subscription(event, info):
    if event:
        return {
            'status': 'Active',
            'event': event,
        }

    return {'status': 'Error'}


async def trigger_event_mutation(_, info):
    await event_queue.put(Event.START_WORKFLOW)
    return {'status': 'Ok'}


async def keep_alive_subscription_mutation(_, info):
    Subscription.keep_alive = datetime.now() + timedelta.seconds(60)
    return {'status': 'Ok'}
