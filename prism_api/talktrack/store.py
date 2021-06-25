from pydantic.types import UUID4

from rexredis import RexRedis

from .entities import (
    TalkTrack,
    TalkTrackId,
    TalkTrackInfo,
)
from prism_api.graphql.entities.types import SessionId


class Store:
    _redis = None

    TALKTRACK_PREFIX = 'talktrack'

    TALKTRACK_INFO_PREFIX = 'talktrack-info'

    @classmethod
    def _get_redis(cls):
        if cls._redis is None or cls._redis.ping() is False:
            cls._redis = RexRedis()
        return cls._redis

    @classmethod
    def _get_talktrack_info_key(cls, talktrack_id: TalkTrackId) -> str:
        return f'{cls.TALKTRACK_INFO_PREFIX}:{talktrack_id}'

    @classmethod
    def _get_talktrack_key(
        cls,
        session_id: SessionId,
        talktrack_uuid: UUID4,
    ) -> str:
        return f'{cls.TALKTRACK_PREFIX}:{session_id}:{talktrack_uuid}'

    @classmethod
    def save_talktrack_info(cls, talktrack_info: TalkTrackInfo):
        redis = cls._get_redis()
        redis.set_val(
            cls._get_talktrack_info_key(talktrack_info.talktrack_id),
            talktrack_info.json(),
        )

    @classmethod
    def get_talktrack_info(cls, talktrack_id: TalkTrackId) -> TalkTrackInfo:
        redis = cls._get_redis()
        data = redis.get_from_json(cls._get_talktrack_info_key(talktrack_id))
        talktrack_info = TalkTrackInfo(**data)
        return talktrack_info

    @classmethod
    def list_talktrack_info(cls) -> list[TalkTrackInfo]:
        redis = cls._get_redis()
        talktrack_keys = redis.find_keys(cls.TALKTRACK_INFO_PREFIX + ':')
        talktrack_list = []
        for talktrack_info_key in talktrack_keys:
            data = redis.get_from_json(talktrack_info_key)
            talktrack_info = TalkTrackInfo(**data)
            talktrack_list.append(talktrack_info)
        return talktrack_list

    @classmethod
    def clear_talktrack_info(cls):
        redis = cls._get_redis()
        talktrack_keys = redis.find_keys(cls.TALKTRACK_INFO_PREFIX + ':')
        redis.delete_keys(*talktrack_keys)

    @classmethod
    def save_talktrack(cls, talktrack: TalkTrack):
        redis = cls._get_redis()
        redis.set_val(
            cls._get_talktrack_key(talktrack.session_id, talktrack.id),
            talktrack.json(),
        )

    @classmethod
    def get_talktrack(
        cls,
        session_id: SessionId,
        talktrack_uuid: UUID4,
    ) -> TalkTrack:
        redis = cls._get_redis()
        talktrack_key = cls._get_talktrack_key(session_id, talktrack_uuid)
        data = redis.get_from_json(talktrack_key)
        talktrack = TalkTrack(**data)
        return talktrack

    @classmethod
    def get_talktrack_queue(cls, session_id: SessionId) -> list[TalkTrack]:
        redis = cls._get_redis()
        keys = redis.find_keys(f'{cls.TALKTRACK_PREFIX}:{session_id}:')
        talktracks = []
        for talktrack_key in keys:
            data = redis.get_from_json(talktrack_key)
            talktrack = TalkTrack(**data)
            talktracks.append(talktrack)
        return talktracks

    @classmethod
    def remove_talktrack(cls, session_id: SessionId, talktrack_uuid: UUID4):
        redis = cls._get_redis()
        talktrack_key = cls._get_talktrack_key(session_id, talktrack_uuid)
        redis.delete_keys(talktrack_key)
