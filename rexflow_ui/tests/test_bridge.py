import unittest
from unittest import mock

import pytest
from gql import Client, gql

from .mocks import (
    MOCK_BRIDGE_URL,
    MOCK_DID,
    MOCK_IID,
    MOCK_TID,
)
from .mocks.rexflow_schema import schema
from .utils import run_async
from rexflow_ui import settings
from rexflow_ui.bridge.gql import REXFlowBridgeGQL
from rexflow_ui.entities.types import (
    Task,
    TaskFieldData,
    TaskStatus,
    Workflow,
    WorkflowStatus,
)

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


mock_task_data = TaskFieldData(
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
    'rexflow_ui.bridge.gql.client.GQLClient._get_client',
    mock_get_client,
)
class TestBridgeIntegration(unittest.TestCase):
    @run_async
    async def test_start_workflow(self):
        workflow = await REXFlowBridgeGQL.start_workflow(
            bridge_url=MOCK_BRIDGE_URL,
        )
        self.assertIsInstance(workflow, Workflow)
        self.assertEqual(MOCK_DID, workflow.did)

    @run_async
    async def test_task_get_data(self):
        workflow = Workflow(
            iid=MOCK_IID,
            did=MOCK_DID,
            status=WorkflowStatus.RUNNING,
        )
        rexflow = REXFlowBridgeGQL(workflow)

        task_ids = [MOCK_TID]
        tasks = await rexflow.get_task_data(task_ids)
        self.assertGreater(len(tasks), 0)
        for task in tasks:
            self.assertIsInstance(task, Task)
            self.assertIn(task.tid, task_ids)

    @run_async
    async def test_task_validate_data(self):
        workflow = Workflow(
            iid=MOCK_IID,
            did=MOCK_DID,
            status=WorkflowStatus.RUNNING,
        )
        rexflow = REXFlowBridgeGQL(workflow)

        result = await rexflow.validate_task_data([
            Task(
                iid=MOCK_IID,
                tid=MOCK_TID,
                data=[mock_task_data],
                status=TaskStatus.UP,
            ),
        ])
        self.assertGreater(len(result.successful), 0)
        for task in result.successful:
            self.assertIsInstance(task, Task)

    @run_async
    async def test_task_save_data(self):
        workflow = Workflow(
            iid=MOCK_IID,
            did=MOCK_DID,
            status=WorkflowStatus.RUNNING,
        )
        rexflow = REXFlowBridgeGQL(workflow)

        result = await rexflow.save_task_data([
            Task(
                iid=MOCK_IID,
                tid=MOCK_TID,
                data=[mock_task_data],
                status=TaskStatus.UP,
            ),
        ])
        self.assertGreater(len(result.successful), 0)
        for task in result.successful:
            self.assertIsInstance(task, Task)

    @run_async
    async def test_task_complete(self):
        workflow = Workflow(
            iid=MOCK_IID,
            did=MOCK_DID,
            status=WorkflowStatus.RUNNING,
        )
        rexflow = REXFlowBridgeGQL(workflow)

        result = await rexflow.complete_task([
            Task(
                iid=MOCK_IID,
                tid=MOCK_TID,
                data=[mock_task_data],
                status=TaskStatus.UP,
            ),
        ])
        self.assertGreater(len(result.successful), 0)
        for task in result.successful:
            self.assertIsInstance(task, Task)

    @run_async
    async def test_cancel_workflow(self):
        workflow = Workflow(
            iid=MOCK_IID,
            did=MOCK_DID,
            status=WorkflowStatus.RUNNING,
        )
        rexflow = REXFlowBridgeGQL(workflow)

        result = await rexflow.cancel_workflow()
        self.assertTrue(result)
