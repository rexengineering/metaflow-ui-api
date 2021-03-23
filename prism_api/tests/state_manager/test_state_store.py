import asyncio
import json
import unittest
from unittest import mock

import pytest

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
