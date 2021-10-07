import unittest
from unittest import mock

import pytest
from gql import Client, gql

from .mocks import (
    MOCK_BRIDGE_URL,
    MOCK_DID,
    MOCK_IID,
    MOCK_TID,
    MOCK_XID,
)
from .mocks.rexflow_schema import schema
from .utils import run_async
from rexflow_ui.bridge.gql import REXFlowBridgeGQL
from rexflow_ui.entities.types import (
    Task,
    TaskFieldData,
    TaskStatus,
    Workflow,
    WorkflowInstanceInfo,
    WorkflowStatus,
)

REXUI_CALLBACK_HOST = 'http://test/callback'


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
@mock.patch(
    'rexflow_ui.bridge.gql.bridge.REXUI_CALLBACK_HOST',
    REXUI_CALLBACK_HOST,
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
    async def test_get_instances(self):
        instances = await REXFlowBridgeGQL.get_instances(
            bridge_url=MOCK_BRIDGE_URL,
        )
        self.assertGreater(len(instances), 0)
        self.assertIsInstance(instances[0], WorkflowInstanceInfo)

    @run_async
    async def test_update_workflow_data(self):
        workflow = Workflow(
            iid=MOCK_IID,
            did=MOCK_DID,
            status=WorkflowStatus.RUNNING,
        )
        rexflow = REXFlowBridgeGQL(workflow)
        updated_workflow = await rexflow.update_workflow_data()
        self.assertIsInstance(updated_workflow, Workflow)
        self.assertEqual(workflow.iid, updated_workflow.iid)

    @run_async
    async def test_get_task_exchange_data(self):
        workflow = Workflow(
            iid=MOCK_IID,
            did=MOCK_DID,
            status=WorkflowStatus.RUNNING,
        )
        rexflow = REXFlowBridgeGQL(workflow)
        task = await rexflow.get_task_exchange_data(MOCK_XID)
        self.assertIsInstance(task, Task)
        self.assertEqual(MOCK_XID, task.xid)

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
    async def test_task_validate_data_exchange(self):
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
                xid=MOCK_XID,
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
    async def test_task_save_data_exchange(self):
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
                xid=MOCK_XID,
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
    async def test_task_complete_exchange(self):
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
                xid=MOCK_XID,
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
