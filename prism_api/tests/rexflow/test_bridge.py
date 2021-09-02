import unittest
from unittest import mock

import pytest
from gql import Client, gql

from ..mocks import (
    MOCK_BRIDGE_URL,
    MOCK_DID,
    MOCK_IID,
    MOCK_TID,
)
from ..mocks.rexflow_schema import schema
from ..utils import run_async
from prism_api import settings
from prism_api.rexflow import bridge

settings.REXUI_CALLBACK_HOST = 'http://test/callback'


@pytest.mark.ci
class TestGraphQLSchema(unittest.TestCase):
    def test_graphql_schema(self):
        client = Client(schema=schema)
        query = gql("""
        query TestVersion {
            version
        }
        """)
        result = client.execute(query)
        expected = {'version': '0.0.0'}
        self.assertEqual(result, expected)


mock_task_data = bridge.TaskFieldData(
    data_id='uname',
    type='TEXT',
    order=1,
    label='username',
    data='',
    encrypted=False,
    validators=[],
)


def mock_get_client(*_):
    print('mocking client')
    return Client(schema=schema)


@pytest.mark.ci
@mock.patch(
    'prism_api.rexflow.bridge.GQLClient._get_client',
    mock_get_client,
)
class TestBridgeIntegration(unittest.TestCase):
    @run_async
    async def test_start_workflow(self):
        workflow = await bridge.REXFlowBridgeGQL.start_workflow(
            bridge_url=MOCK_BRIDGE_URL,
        )
        self.assertIsInstance(workflow, bridge.Workflow)
        self.assertEqual(MOCK_DID, workflow.did)

    @run_async
    async def test_task_get_data(self):
        workflow = bridge.Workflow(
            iid=MOCK_IID,
            did=MOCK_DID,
            status=bridge.WorkflowStatus.RUNNING,
        )
        rexflow = bridge.REXFlowBridgeGQL(workflow)

        task_ids = [MOCK_TID]
        tasks = await rexflow.get_task_data(task_ids)
        self.assertGreater(len(tasks), 0)
        for task in tasks:
            self.assertIsInstance(task, bridge.Task)
            self.assertIn(task.tid, task_ids)

    @run_async
    async def test_task_validate_data(self):
        workflow = bridge.Workflow(
            iid=MOCK_IID,
            did=MOCK_DID,
            status=bridge.WorkflowStatus.RUNNING,
        )
        rexflow = bridge.REXFlowBridgeGQL(workflow)

        result = await rexflow.validate_task_data([
            bridge.Task(
                iid=MOCK_IID,
                tid=MOCK_TID,
                data=[mock_task_data],
                status=bridge.TaskStatus.UP,
            ),
        ])
        self.assertGreater(len(result.successful), 0)
        for task in result.successful:
            self.assertIsInstance(task, bridge.Task)

    @run_async
    async def test_task_save_data(self):
        workflow = bridge.Workflow(
            iid=MOCK_IID,
            did=MOCK_DID,
            status=bridge.WorkflowStatus.RUNNING,
        )
        rexflow = bridge.REXFlowBridgeGQL(workflow)

        result = await rexflow.save_task_data([
            bridge.Task(
                iid=MOCK_IID,
                tid=MOCK_TID,
                data=[mock_task_data],
                status=bridge.TaskStatus.UP,
            ),
        ])
        self.assertGreater(len(result.successful), 0)
        for task in result.successful:
            self.assertIsInstance(task, bridge.Task)

    @run_async
    async def test_task_complete(self):
        workflow = bridge.Workflow(
            iid=MOCK_IID,
            did=MOCK_DID,
            status=bridge.WorkflowStatus.RUNNING,
        )
        rexflow = bridge.REXFlowBridgeGQL(workflow)

        result = await rexflow.complete_task([
            bridge.Task(
                iid=MOCK_IID,
                tid=MOCK_TID,
                data=[mock_task_data],
                status=bridge.TaskStatus.UP,
            ),
        ])
        self.assertGreater(len(result.successful), 0)
        for task in result.successful:
            self.assertIsInstance(task, bridge.Task)

    @run_async
    async def test_cancel_workflow(self):
        workflow = bridge.Workflow(
            iid=MOCK_IID,
            did=MOCK_DID,
            status=bridge.WorkflowStatus.RUNNING,
        )
        rexflow = bridge.REXFlowBridgeGQL(workflow)

        result = await rexflow.cancel_workflow()
        self.assertTrue(result)
