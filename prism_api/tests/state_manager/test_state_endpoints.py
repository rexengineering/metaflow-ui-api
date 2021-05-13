import unittest
from unittest import mock

from fastapi.testclient import TestClient
import pytest

from prism_api.app import app
from ..mocks.state_store import FakeStore


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
class TestStateClient(unittest.TestCase):
    endpoint = '/state/' + client_id

    def setUp(self) -> None:
        self.client = TestClient(app)

    @mock.patch('prism_api.state_manager.store.api.Store', FakeStore)
    def test_save_state(self):
        response = self.client.post(
            self.endpoint,
            json=fake_state,
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), fake_state)

    @mock.patch('prism_api.state_manager.store.api.Store', FakeStore)
    def test_read_state(self):
        response = self.client.get(self.endpoint)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), FakeStore.default)
