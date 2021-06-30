from enum import Enum
from typing import List, Optional

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
    title: str
    text: str
    workflow_name: Optional[str]
    actions: List[TalkTrackAction]


class TalkTrack(BaseModel):
    id: UUID4
    session_id: SessionId
    order: int
    details: TalkTrackInfo
    workflow: Optional[Workflow]
    status: TalkTrackStatus
