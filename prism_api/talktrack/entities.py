from enum import Enum
from typing import Dict, List, Optional

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


class TalkTrackStep(BaseModel):
    title: str
    text: str
    order: int
    workflow_name: Optional[str]
    actions: List[TalkTrackAction] = []


class TalkTrackInfo(BaseModel):
    talktrack_id: TalkTrackId
    title: str
    steps: List[TalkTrackStep]

    def get_step(self, number: int) -> Optional[TalkTrackStep]:
        for step in self.steps:
            if step.order == number:
                return step

        return None


class TalkTrack(BaseModel):
    id: UUID4
    session_id: SessionId
    order: int
    current_step: int = 1
    details: TalkTrackInfo
    status: TalkTrackStatus

    _workflows_dict: Dict[int, Workflow] = {}

    @property
    def workflows(self) -> List[Workflow]:
        return list(self._workflows_dict.values())

    def add_workflow(self, step_number: int, workflow: Workflow):
        self._workflows_dict[step_number] = workflow

    def workflow_not_started(self, step_number: int):
        return step_number not in self._workflows_dict
