import unittest
from unittest import mock

from ..mocks import rexflow_api
from ..mocks.talktrack_store import FakeStore
from ..utils import run_async
from prism_api.talktrack.actions import (
    load_talktracks,
    list_talktracks,
    start_talktrack,
    get_talktrack_queue,
    end_talktrack,
)
from prism_api.talktrack.entities import (
    TalkTrack,
    TalkTrackInfo,
    TalkTrackStatus,
)


SESSION_ID = 'testuser'

mock_talktrack_info = TalkTrackInfo(
    talktrack_id='talktrack-123',
    text='this is a test',
    workflow_name='process',
    actions=[],
)


@mock.patch('prism_api.talktrack.actions.Store', FakeStore)
class TestTalkTrackLoader(unittest.TestCase):
    def test_load_talktracks(self):
        file_mock = mock.mock_open(read_data=mock_talktrack_info.json())
        with mock.patch('prism_api.talktrack.provider.open', file_mock):
            load_talktracks()
        talktrack_info = FakeStore.list_talktrack_info()
        self.assertGreater(len(talktrack_info), 0)
        self.assertIn(mock_talktrack_info, talktrack_info)


@mock.patch('prism_api.talktrack.actions.Store', FakeStore)
@mock.patch(
    'prism_api.talktrack.actions.rexflow',
    rexflow_api,
)
class TestTalkTrackActions(unittest.TestCase):
    def setUp(self):
        FakeStore.save_talktrack_info(mock_talktrack_info)

    def tearDown(self):
        FakeStore.clear_talktrack_info()

    def test_list_talktracks(self):
        talktrack_info_store = FakeStore.list_talktrack_info()
        talktrack_info = list_talktracks()
        self.assertEqual(talktrack_info, talktrack_info_store)

    @run_async
    async def test_start_talktrack(self):
        self.assertEqual(len(FakeStore.get_talktrack_queue(SESSION_ID)), 0)
        talktrack = await start_talktrack(
            SESSION_ID,
            mock_talktrack_info.talktrack_id,
        )
        self.assertIsInstance(talktrack, TalkTrack)
        self.assertEqual(talktrack.status, TalkTrackStatus.ACTIVE)
        self.assertEqual(len(FakeStore.get_talktrack_queue(SESSION_ID)), 1)

    @run_async
    async def test_talktrack_queue(self):
        self.assertEqual(len(FakeStore.get_talktrack_queue(SESSION_ID)), 0)
        active_talktrack = await start_talktrack(
            SESSION_ID,
            mock_talktrack_info.talktrack_id,
        )
        self.assertEqual(len(FakeStore.get_talktrack_queue(SESSION_ID)), 1)

        queued_talktrack = await start_talktrack(
            SESSION_ID,
            mock_talktrack_info.talktrack_id,
        )
        self.assertEqual(queued_talktrack.status, TalkTrackStatus.QUEUE)
        self.assertEqual(len(FakeStore.get_talktrack_queue(SESSION_ID)), 2)

        talktrack_queue = get_talktrack_queue(SESSION_ID)
        self.assertIn(active_talktrack, talktrack_queue)
        self.assertIn(queued_talktrack, talktrack_queue)
        self.assertEqual(
            talktrack_queue,
            FakeStore.get_talktrack_queue(SESSION_ID),
        )

    @run_async
    async def test_end_talktrack(self):
        talktrack = await start_talktrack(
            SESSION_ID,
            mock_talktrack_info.talktrack_id,
        )
        self.assertEqual(len(FakeStore.get_talktrack_queue(SESSION_ID)), 1)
        end_talktrack(talktrack.id)
        self.assertEqual(len(FakeStore.get_talktrack_queue(SESSION_ID)), 0)
