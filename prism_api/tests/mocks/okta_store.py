
from typing import Union
from unittest import mock

from .okta_entities import (
    mock_jwks_response
)
from prism_api.okta.entities import JWKSResponse


class Store:
    has_stored_keys = True

    save_jwks = mock.Mock()

    @classmethod
    def get_jwks(cls) -> Union[JWKSResponse, None]:
        if cls.has_stored_keys:
            return mock_jwks_response()

        return None
