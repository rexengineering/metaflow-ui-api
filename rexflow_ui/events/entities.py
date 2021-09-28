from enum import Enum

from pydantic import BaseModel


class Event(str, Enum):
    START_WORKFLOW = 'START_WORKFLOW'
    UPDATE_WORKFLOW = 'UPDATE_WORKFLOW'
    FINISH_WORKFLOW = 'FINISH_WORKFLOW'

    START_TASK = 'START_TASK'
    UPDATE_TASK = 'UPDATE_TASK'
    FINISH_TASK = 'FINISH_TASK'

    START_BROADCAST = 'START_BROADCAST'
    FINISH_BROADCAST = 'FINISH_BROADCAST'
    ERROR_BROADCAST = 'ERROR_BROADCAST'


class EventWrapper(BaseModel):
    event: Event
    data: dict = {}
