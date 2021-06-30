import unittest
from unittest import mock
from uuid import uuid4

from rexredis import RexRedis

from ..mocks.rexflow_entities import mock_workflow
from prism_api.talktrack.entities import (
    TalkTrack,
    TalkTrackInfo,
    TalkTrackStatus,
)
from prism_api.talktrack.store import Store

REXREDIS_PATH = 'prism_api.talktrack.store.Store._get_redis'

SESSION_ID = 'testuser'

mock_talktrack_info = TalkTrackInfo(
            talktrack_id='talktrack-123',
            title='test',
            text='this is a test',
            workflow_name='process',
            actions=[],
        )

mock_talktrack = TalkTrack(
    id=uuid4(),
    session_id=SESSION_ID,
    order=1,
    details=mock_talktrack_info,
    workflow=mock_workflow(),
    status=TalkTrackStatus.ACTIVE,
)


def mock_redis_client():
    return mock.MagicMock(spec=RexRedis)


class TestTalkTrackStore(unittest.TestCase):
    def setUp(self):
        self.mock_redis: RexRedis = mock_redis_client()

    def test_save_talktrack_info(self):
        with mock.patch(REXREDIS_PATH, return_value=self.mock_redis):
            Store.save_talktrack_info(mock_talktrack_info)

        self.mock_redis.set_val.assert_called_with(
            Store._get_talktrack_info_key(mock_talktrack_info.talktrack_id),
            mock_talktrack_info.json(),
        )

    def test_get_talktrack_info(self):
        with mock.patch(REXREDIS_PATH, return_value=self.mock_redis):
            self.mock_redis.get_from_json.return_value = mock_talktrack_info.dict()  # noqa: E501
            Store.get_talktrack_info(mock_talktrack_info.talktrack_id)

        talktrack_info_key = Store._get_talktrack_info_key(
            mock_talktrack_info.talktrack_id,
        )
        self.mock_redis.get_from_json.assert_called_with(talktrack_info_key)

    def test_list_talktrack_info(self):
        talktrack_info_key = Store._get_talktrack_info_key(
            mock_talktrack_info.talktrack_id,
        )

        with mock.patch(REXREDIS_PATH, return_value=self.mock_redis):
            self.mock_redis.find_keys.return_value = [talktrack_info_key]
            self.mock_redis.get_from_json.return_value = mock_talktrack_info.dict()  # noqa: E501
            Store.list_talktrack_info()

        self.mock_redis.find_keys.assert_called()
        self.mock_redis.get_from_json.assert_called_with(talktrack_info_key)

    def test_clear_talktrack_info(self):
        talktrack_info_key = Store._get_talktrack_info_key(
            mock_talktrack_info.talktrack_id,
        )
        with mock.patch(REXREDIS_PATH, return_value=self.mock_redis):
            self.mock_redis.find_keys.return_value = [talktrack_info_key]
            Store.clear_talktrack_info()

        self.mock_redis.delete_keys.assert_called_with(talktrack_info_key)

    def test_save_talktrack(self):
        talktrack_key = Store._get_talktrack_key(
            SESSION_ID,
            mock_talktrack.id,
        )
        with mock.patch(REXREDIS_PATH, return_value=self.mock_redis):
            Store.save_talktrack(mock_talktrack)

        self.mock_redis.set_val.assert_called_with(
            talktrack_key,
            mock_talktrack.json(),
        )

    def test_get_talktrack(self):
        talktrack_key = Store._get_talktrack_key(
            SESSION_ID,
            mock_talktrack.id,
        )
        with mock.patch(REXREDIS_PATH, return_value=self.mock_redis):
            self.mock_redis.get_from_json.return_value = mock_talktrack.dict()
            Store.get_talktrack(SESSION_ID, mock_talktrack.id)

        self.mock_redis.get_from_json.assert_called_with(talktrack_key)

    def test_get_talktrack_queue(self):
        talktrack_key = Store._get_talktrack_key(
            SESSION_ID,
            mock_talktrack.id,
        )
        with mock.patch(REXREDIS_PATH, return_value=self.mock_redis):
            self.mock_redis.find_keys.return_value = [talktrack_key]
            self.mock_redis.get_from_json.return_value = mock_talktrack.dict()
            Store.get_talktrack_queue(SESSION_ID)

        self.mock_redis.get_from_json.assert_called_with(talktrack_key)

    def test_remove_talktrack(self):
        talktrack_key = Store._get_talktrack_key(
            SESSION_ID,
            mock_talktrack.id,
        )
        with mock.patch(REXREDIS_PATH, return_value=self.mock_redis):
            Store.remove_talktrack(SESSION_ID, mock_talktrack.id)

        self.mock_redis.delete_keys.assert_called_with(talktrack_key)
