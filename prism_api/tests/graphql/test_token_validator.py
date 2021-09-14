import unittest
from unittest import mock

import pytest

from ..utils import run_async
from ..mocks.graphql_info import MockInfo
from ..mocks.okta_entities import Token, mock_info_with_token, mock_token
from prism_api.graphql.errors import HttpUnauthorizedError
from prism_api.graphql.decorators import (
    _verify_access_token,
    ValidationError,
    JWTError,
)


async def mock_validate_access_token(token: str):
    return mock_token()


async def mock_validation_error(token: str):
    raise ValidationError([], Token)


async def mock_jwt_error(token: str):
    raise JWTError


@pytest.mark.ci
@mock.patch(
    'prism_api.graphql.decorators.settings.DISABLE_AUTHENTICATION',
    True,
)
class TestDisabledAuthentication(unittest.TestCase):
    @run_async
    async def test_disabled_authentication(self):
        info = mock_info_with_token()
        await _verify_access_token(info)
        self.assertIsNone(info.context['access_token'])
        self.assertEqual(info.context['session_id'], 'anon')


@pytest.mark.ci
@mock.patch(
    'prism_api.graphql.decorators.settings.DISABLE_AUTHENTICATION',
    False,
)
class TestTokenValidator(unittest.TestCase):
    @run_async
    async def test_missing_access_token(self):
        with self.assertRaises(HttpUnauthorizedError):
            await _verify_access_token(MockInfo())

    @run_async
    @mock.patch(
        'prism_api.graphql.decorators.validate_access_token',
        mock_validate_access_token,
    )
    async def test_verify_access_token(self):
        info = mock_info_with_token()
        await _verify_access_token(info)
        self.assertIsInstance(info.context['access_token'], Token)
        self.assertEqual(
            info.context['access_token'].sub,
            info.context['session_id'],
        )

    @run_async
    @mock.patch(
        'prism_api.graphql.decorators.validate_access_token',
        mock_validation_error,
    )
    async def test_validation_error(self):
        with self.assertRaises(HttpUnauthorizedError):
            await _verify_access_token(mock_info_with_token())

    @run_async
    @mock.patch(
        'prism_api.graphql.decorators.validate_access_token',
        mock_jwt_error,
    )
    async def test_jwt_error(self):
        with self.assertRaises(HttpUnauthorizedError):
            await _verify_access_token(mock_info_with_token())
