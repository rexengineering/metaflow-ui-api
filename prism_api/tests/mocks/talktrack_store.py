from pydantic.types import UUID4

from prism_api.graphql.entities.types import SessionId
from prism_api.talktrack.entities import (
    TalkTrack,
    TalkTrackId,
    TalkTrackInfo,
)


class FakeStore:
    _talktrack_info_store: dict[TalkTrackId, TalkTrackInfo] = {}
    _talktrack_store: dict[UUID4, TalkTrack] = {}

    @classmethod
    def save_talktrack_info(cls, talktrack_info: TalkTrackInfo):
        cls._talktrack_info_store[talktrack_info.talktrack_id] = talktrack_info

    @classmethod
    def get_talktrack_info(cls, talktrack_id: TalkTrackId) -> TalkTrackInfo:
        return cls._talktrack_info_store[talktrack_id]

    @classmethod
    def list_talktrack_info(cls) -> list[TalkTrackInfo]:
        return [
            talktrack_info
            for talktrack_info
            in cls._talktrack_info_store.values()
        ]

    @classmethod
    def clear_talktrack_info(cls):
        cls._talktrack_info_store = {}
        cls._talktrack_store = {}

    @classmethod
    def save_talktrack(cls, talktrack: TalkTrack):
        cls._talktrack_store[talktrack.id] = talktrack

    @classmethod
    def get_talktrack(cls, talktrack_uuid: UUID4) -> TalkTrack:
        return cls._talktrack_store[talktrack_uuid]

    @classmethod
    def get_talktrack_queue(cls, session_id: SessionId) -> list[TalkTrack]:
        return [
            talktrack
            for talktrack
            in cls._talktrack_store.values()
            if talktrack.session_id == session_id
        ]

    @classmethod
    def remove_talktrack(cls, talktrack_uuid: UUID4):
        del cls._talktrack_store[talktrack_uuid]
