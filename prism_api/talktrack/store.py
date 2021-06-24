from pydantic.types import UUID4

from prism_api.graphql.entities.types import SessionId
from .entities import (
    TalkTrack,
    TalkTrackId,
    TalkTrackInfo,
)


class Store:
    @classmethod
    def save_talktrack_info(cls, talktrack_info: TalkTrackInfo):
        ...

    @classmethod
    def get_talktrack_info(cls, talktrack_id: TalkTrackId) -> TalkTrackInfo:
        ...

    @classmethod
    def list_talktrack_info(cls) -> list[TalkTrackInfo]:
        ...

    @classmethod
    def clear_talktrack_info(cls):
        ...

    @classmethod
    def save_talktrack(cls, talktrack: TalkTrack):
        ...

    @classmethod
    def get_talktrack(cls, taltrack_uuid: UUID4) -> TalkTrack:
        ...

    @classmethod
    def get_talktrack_queue(cls, session_id: SessionId) -> list[TalkTrack]:
        ...

    @classmethod
    def remove_talktrack(cls, talktrack_uuid: UUID4):
        ...
