import unittest
from unittest import mock

import pytest
from httpx import ConnectError

from ..utils import run_async
from ..mocks.okta_entities import mock_jwks, mock_jwks_response
from ..mocks.okta_store import Store
from prism_api.okta.actions import (
    get_json_web_keys,
    OktaError,
)


def _raise_error(*args, **kwargs):
    raise ConnectError(request=None, message='Test')


@pytest.mark.ci
class TestActions(unittest.TestCase):
    @run_async
    @mock.patch('prism_api.okta.actions.Store.has_stored_keys', False)
    @mock.patch('prism_api.okta.actions.Store', Store)
    async def test_get_json_web_keys_empty(self):
        jwks_response = mock_jwks_response()
        with mock.patch('prism_api.okta.actions.AsyncClient.get') as get:
            get.return_value = mock.Mock()
            get.return_value.json.return_value = jwks_response.dict()
            keys = await get_json_web_keys()
            get.assert_called()
            Store.save_jwks.assert_called()
        self.assertGreater(len(keys), 0)
        self.assertIn(jwks_response.keys[0].kid, keys)

    @run_async
    @mock.patch('prism_api.okta.actions.Store', Store)
    async def test_get_json_web_keys_store(self):
        jwks = mock_jwks()
        keys = await get_json_web_keys()
        self.assertGreater(len(keys), 0)
        self.assertIn(jwks.kid, keys)

    @run_async
    @mock.patch('prism_api.okta.actions.Store.has_stored_keys', False)
    @mock.patch('prism_api.okta.actions.Store', Store)
    async def test_get_json_web_keys_error(self):
        with mock.patch('prism_api.okta.actions.AsyncClient.get') as get:
            get.side_effect = _raise_error
            with self.assertRaises(OktaError):
                await get_json_web_keys()
