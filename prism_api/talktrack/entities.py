from enum import Enum
from typing import List

from pydantic import BaseModel
from pydantic.types import UUID4

from prism_api.graphql.entities.types import SessionId
from prism_api.rexflow.entities.types import (
    Workflow,
)


class TalkTrackId(str):
    """Identifier for a Talk Track"""


class TalkTrackStatus(str, Enum):
    ACTIVE = 'ACTIVE'
    QUEUE = 'QUEUE'


class TalkTrackAction(BaseModel):
    label: str
    talktrack_id: TalkTrackId


class TalkTrackInfo(BaseModel):
    talktrack_id: TalkTrackId
    text: str
    workflow_name: str
    actions: List[TalkTrackAction]


class TalkTrack(BaseModel):
    id: UUID4
    session_id: SessionId
    details: TalkTrackInfo
    workflow: Workflow
    status: TalkTrackStatus
