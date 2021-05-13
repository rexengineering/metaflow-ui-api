import unittest
from unittest import mock

from gql import Client, gql

from prism_api import settings
from prism_api.rexflow import bridge
from ..mocks.rexflow_schema import (
    MOCK_DID,
    MOCK_IID,
    MOCK_TID,
    schema,
)
from ..utils import run_async

settings.REXUI_CALLBACK_HOST = 'http://test/callback'


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


mock_task_data = bridge.e.TaskFieldData(
    dataId='uname',
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


@mock.patch(
    'prism_api.rexflow.bridge.REXFlowBridgeGQL.get_client',
    mock_get_client,
)
class TestBridgeIntegration(unittest.TestCase):
    @run_async
    async def test_start_workflow(self):
        workflow = await bridge.REXFlowBridgeGQL.start_workflow(
            deployment_id=MOCK_DID,
        )
        self.assertIsInstance(workflow, bridge.e.Workflow)
        self.assertEqual(MOCK_DID, workflow.did)

    @run_async
    async def test_task_get_data(self):
        workflow = bridge.e.Workflow(
            iid=MOCK_IID,
            did=MOCK_DID,
            status=bridge.e.WorkflowStatus.RUNNING,
        )
        rexflow = bridge.REXFlowBridgeGQL(workflow)

        task_ids = [MOCK_TID]
        tasks = await rexflow.get_task_data(task_ids)
        self.assertGreater(len(tasks), 0)
        for task in tasks:
            self.assertIsInstance(task, bridge.e.Task)
            self.assertIn(task.tid, task_ids)

    @run_async
    async def test_task_validate_data(self):
        workflow = bridge.e.Workflow(
            iid=MOCK_IID,
            did=MOCK_DID,
            status=bridge.e.WorkflowStatus.RUNNING,
        )
        rexflow = bridge.REXFlowBridgeGQL(workflow)

        tasks = await rexflow.validate_task_data([
            bridge.e.Task(
                iid=MOCK_IID,
                tid=MOCK_TID,
                data=[mock_task_data],
                status=bridge.e.TaskStatus.UP,
            ),
        ])
        self.assertGreater(len(tasks), 0)
        for task in tasks:
            self.assertIsInstance(task, bridge.e.Task)

    @run_async
    async def test_task_save_data(self):
        workflow = bridge.e.Workflow(
            iid=MOCK_IID,
            did=MOCK_DID,
            status=bridge.e.WorkflowStatus.RUNNING,
        )
        rexflow = bridge.REXFlowBridgeGQL(workflow)

        tasks = await rexflow.save_task_data([
            bridge.e.Task(
                iid=MOCK_IID,
                tid=MOCK_TID,
                data=[mock_task_data],
                status=bridge.e.TaskStatus.UP,
            ),
        ])
        self.assertGreater(len(tasks), 0)
        for task in tasks:
            self.assertIsInstance(task, bridge.e.Task)

    @run_async
    async def test_task_complete(self):
        workflow = bridge.e.Workflow(
            iid=MOCK_IID,
            did=MOCK_DID,
            status=bridge.e.WorkflowStatus.RUNNING,
        )
        rexflow = bridge.REXFlowBridgeGQL(workflow)

        tasks = await rexflow.complete_task([
            bridge.e.Task(
                iid=MOCK_IID,
                tid=MOCK_TID,
                data=[mock_task_data],
                status=bridge.e.TaskStatus.UP,
            ),
        ])
        self.assertGreater(len(tasks), 0)
        for task in tasks:
            self.assertIsInstance(task, bridge.e.Task)
