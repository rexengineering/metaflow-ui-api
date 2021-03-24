import asyncio
import json
import unittest
from unittest import mock

import pytest
from rexredis import RexRedis

from prism_api.state_manager.store import api as store
from ..utils import FakeStore


FakeStore.sleep_time = 0.1

client_id = 'test123'

fake_state = {
    'status': 'ok',
    'elements': {
        'first': 'ok',
        'second': 'ok',
        'third': 'ok',
    }
}


@pytest.mark.ci
class TestStateStore(unittest.TestCase):
    def test_serialize_state(self):
        serialized_state = store.serialize_state(fake_state)
        self.assertEqual(serialized_state, json.dumps(fake_state))

    def test_deserialize_state(self):
        serialized_state = json.dumps(fake_state)
        state = store.deserialize_state(serialized_state)
        self.assertEqual(state, fake_state)

    @mock.patch('prism_api.state_manager.store.api.Store', FakeStore)
    def test_save_state(self):
        state = asyncio.run(store.save_state(client_id, fake_state))
        self.assertEqual(state, fake_state)

    @mock.patch('prism_api.state_manager.store.api.Store', FakeStore)
    def test_read_state(self):
        state = asyncio.run(store.read_state(client_id))
        self.assertEqual(state, FakeStore.default)


@pytest.mark.ci
class TestRedisStore(unittest.TestCase):
    def get_mock_instance(self):
        mockInstance = mock.MagicMock(spec=RexRedis)
        mockInstance.get_val.return_value = json.dumps(fake_state)
        return mockInstance

    def test_save_redis(self):
        with mock.patch(
            'prism_api.state_manager.store.adapters.RexRedis',
            return_value=self.get_mock_instance(),
        ):
            state = asyncio.run(store.save_state(client_id, fake_state))
            self.assertEqual(state, fake_state)

    def test_read_redis(self):
        with mock.patch(
            'prism_api.state_manager.store.adapters.RexRedis',
            return_value=self.get_mock_instance(),
        ):
            state = asyncio.run(store.read_state(client_id))
            self.assertEqual(state, fake_state)
