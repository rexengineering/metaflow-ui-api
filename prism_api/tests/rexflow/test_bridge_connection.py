import unittest
from unittest import mock


from ..utils import run_async
from ..mocks import MOCK_DID
from prism_api.rexflow.bridge import REXFlowBridgeGQL
from prism_api.rexflow.errors import BridgeNotReachableError
from prism_api.rexflow.api import _refresh_instance


FAKE_REXFLOW_HOST = 'http://ui-bridge.example'


class TestBridgeConnection(unittest.TestCase):

    @run_async
    @mock.patch(
        'prism_api.rexflow.bridge.settings.REXFLOW_HOST',
        FAKE_REXFLOW_HOST,
    )
    async def test_bridge_connection_failure(self):
        with self.assertRaises(BridgeNotReachableError):
            await REXFlowBridgeGQL.start_workflow(MOCK_DID)

        with self.assertRaises(BridgeNotReachableError):
            await REXFlowBridgeGQL.get_instances(MOCK_DID)

    @run_async
    @mock.patch(
        'prism_api.rexflow.bridge.settings.REXFLOW_HOST',
        FAKE_REXFLOW_HOST,
    )
    async def test_api_bridge_connection_failure(self):
        with self.assertRaises(BridgeNotReachableError):
            await REXFlowBridgeGQL.get_instances(MOCK_DID)

        # Should not trigger error
        await _refresh_instance(MOCK_DID)
