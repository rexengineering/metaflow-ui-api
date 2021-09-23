import unittest
from unittest import mock

import pytest

from .utils import run_async
from .mocks import MOCK_BRIDGE_URL, MOCK_DID, MOCK_IID, MOCK_NAME, MOCK_TID
from .mocks.rexflow_entities import (
    mock_task,
    mock_task_change,
    mock_workflow,
)
from rexflow_ui import api
from rexflow_ui.bridge.gql import REXFlowBridgeGQL
from rexflow_ui.errors import BridgeNotReachableError
from rexflow_ui.entities.types import WorkflowDeployment
from rexflow_ui.store.memory import Store


async def get_deployments():
    return [
        WorkflowDeployment(
            name=MOCK_NAME,
            deployments=[MOCK_DID],
            bridge_url=MOCK_BRIDGE_URL,
        ),
    ]


@mock.patch('rexflow_ui.api.Store', Store)
@mock.patch('rexflow_ui.api.get_deployments', get_deployments)
@pytest.mark.ci
class TestBridgeConnection(unittest.TestCase):

    def tearDown(self):
        Store.clear()

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
    async def test_api_bridge_connection_failure(self):
        # Should not trigger error
        await api._refresh_instance(MOCK_NAME, MOCK_DID, MOCK_BRIDGE_URL)

        with self.assertRaises(BridgeNotReachableError):
            await api.start_workflow(MOCK_DID)

        workflow = mock_workflow()
        await api._refresh_workflow(workflow)

        Store.add_workflow(workflow)
        with self.assertRaises(BridgeNotReachableError):
            await api.start_tasks(MOCK_IID, [MOCK_TID])

        task = mock_task()
        Store.add_task(task)
        task_change = mock_task_change()

        result = await api._validate_tasks(MOCK_IID, [task_change])
        self.assertGreater(len(result.errors), 0)
        self.assertEqual(len(result.successful), 0)

        result = await api._save_tasks(MOCK_IID, [task_change])
        self.assertGreater(len(result.errors), 0)
        self.assertEqual(len(result.successful), 0)

        result = await api._complete_tasks(MOCK_IID, [task_change])
        self.assertGreater(len(result.errors), 0)
        self.assertEqual(len(result.successful), 0)
