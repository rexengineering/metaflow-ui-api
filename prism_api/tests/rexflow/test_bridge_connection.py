import unittest
from unittest import mock

import pytest

from ..utils import run_async
from ..mocks import MOCK_DID, MOCK_IID, MOCK_TID
from ..mocks.rexflow_entities import (
    mock_task,
    mock_task_change,
    mock_workflow,
)
from prism_api.rexflow import api
from prism_api.rexflow.bridge import REXFlowBridgeGQL
from prism_api.rexflow.errors import BridgeNotReachableError
from prism_api.rexflow.store import Store


FAKE_REXFLOW_HOST = 'http://ui-bridge.example'


@mock.patch(
    'prism_api.rexflow.bridge.settings.REXFLOW_HOST',
    FAKE_REXFLOW_HOST,
)
@pytest.mark.ci
class TestBridgeConnection(unittest.TestCase):

    @run_async
    async def test_bridge_class_methods_connection_failure(self):
        with self.assertRaises(BridgeNotReachableError):
            await REXFlowBridgeGQL.start_workflow(MOCK_DID)

        with self.assertRaises(BridgeNotReachableError):
            await REXFlowBridgeGQL.get_instances(MOCK_DID)

    @run_async
    async def test_bridge_instance_connection_failure(self):
        workflow = mock_workflow()
        bridge = REXFlowBridgeGQL(workflow)

        with self.assertRaises(BridgeNotReachableError):
            await bridge.get_task_data([MOCK_TID])

        with self.assertRaises(BridgeNotReachableError):
            task = mock_task()
            await bridge.validate_task_data([task])

        with self.assertRaises(BridgeNotReachableError):
            task = mock_task()
            await bridge.save_task_data([task])

        with self.assertRaises(BridgeNotReachableError):
            task = mock_task()
            await bridge.complete_task([task])

    @run_async
    @pytest.mark.xfail(
        reason='missing error handling',
        raises=BridgeNotReachableError,
    )
    async def test_api_bridge_connection_failure(self):
        with self.assertRaises(BridgeNotReachableError):
            await REXFlowBridgeGQL.start_workflow(MOCK_DID)

        # Should not trigger error
        await api.start_workflow(MOCK_DID)
        await api._refresh_instance(MOCK_DID)

        workflow = mock_workflow()
        await api._refresh_workflow(workflow)

        Store.add_workflow(workflow)
        await api.get_task(MOCK_IID, MOCK_TID)

        task = mock_task()
        Store.add_task(task)
        task_change = mock_task_change()
        await api._validate_tasks(MOCK_IID, [task_change])
        await api._save_tasks(MOCK_IID, [task_change])
        await api._complete_tasks(MOCK_IID, [task_change])
