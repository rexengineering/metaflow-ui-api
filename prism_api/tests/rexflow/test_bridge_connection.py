from prism_api.rexflow.entities.types import WorkflowDeployment
import unittest
from unittest import mock

import pytest

from ..utils import run_async
from ..mocks import MOCK_DID, MOCK_IID, MOCK_NAME, MOCK_TID
from ..mocks.rexflow_entities import (
    mock_task,
    mock_task_change,
    mock_workflow,
)
from prism_api.rexflow import api
from prism_api.rexflow.bridge import REXFlowBridgeGQL
from prism_api.rexflow.errors import BridgeNotReachableError
from prism_api.rexflow.store.memory import Store


FAKE_REXFLOW_HOST = 'http://ui-bridge.example'


async def get_deployments():
    return [
        WorkflowDeployment(
            name=MOCK_NAME,
            deployments=[MOCK_DID],
            bridge_url='',
        ),
    ]


@mock.patch(
    'prism_api.rexflow.bridge.settings.REXFLOW_HOST',
    FAKE_REXFLOW_HOST,
)
@mock.patch('prism_api.rexflow.api.Store', Store)
@mock.patch('prism_api.rexflow.api.get_deployments', get_deployments)
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
        await api._refresh_instance(MOCK_NAME, MOCK_DID)

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
