import unittest
from unittest import mock

import pytest

from ..mocks import MOCK_BRIDGE_URL, MOCK_DID, MOCK_NAME, MOCK_TID
from ..mocks.rexflow_bridge import FakeREXFlowBridge
from ..utils import run_async
from prism_api.rexflow import api
from prism_api.rexflow.entities.types import MetaData, WorkflowDeployment
from prism_api.rexflow.entities.wrappers import TaskChange, TaskDataChange
from prism_api.rexflow.store.memory import Store


FakeREXFlowBridge.sleep_time = 0.1
FakeREXFlowBridge.Store = Store


async def get_deployments():
    return [
        WorkflowDeployment(
            name=MOCK_NAME,
            deployments=[MOCK_DID],
            bridge_url=MOCK_BRIDGE_URL,
        ),
    ]


@pytest.mark.ci
class TestWorkflow(unittest.TestCase):
    def tearDown(self):
        Store.clear()

    @run_async
    @mock.patch('prism_api.rexflow.api.Store', Store)
    @mock.patch('prism_api.rexflow.api.REXFlowBridge', FakeREXFlowBridge)
    @mock.patch('prism_api.rexflow.api.get_deployments', get_deployments)
    async def test_happy_workflow(self):
        metadata = [MetaData(key='session_id', value='anon')]
        # Instance a new workflow
        workflow = await api.start_workflow(
            deployment_id=MOCK_DID,
            metadata=metadata,
        )
        self.assertIsNotNone(workflow)
        self.assertEqual(len(workflow.tasks), 0)
        self.assertIn(workflow, await api.get_active_workflows('anon', []))

        created = await api.start_tasks(workflow.iid, [MOCK_TID])
        new_task = created.pop()
        workflow = api.Store.get_workflow(workflow.iid)
        self.assertIn(new_task, workflow.tasks)

        await api.refresh_workflows()
        self.assertGreater(len(workflow.tasks), 0)
        self.assertIn(new_task, workflow.tasks)

        # Get current workflow task
        task = workflow.tasks[0]
        self.assertIsNotNone(task)

        answer = 'this is the answer'
        # Answer all questions
        for field in task.data:
            field.data = answer

        # Validate the form
        validated_tasks = await api.validate_tasks([
            TaskChange(
                iid=task.iid,
                tid=task.tid,
                data=[
                    TaskDataChange(
                        dataId=field.data_id,
                        data=field.data
                    )
                    for field in task.data
                ],
            )
        ])
        self.assertIn(task, validated_tasks.successful)
        self.assertEqual(answer, validated_tasks.successful[0].data[0].data)

        # Save the form
        saved_task = await api.save_tasks([
            TaskChange(
                iid=task.iid,
                tid=task.tid,
                data=[
                    TaskDataChange(
                        dataId=field.data_id,
                        data=field.data
                    )
                    for field in task.data
                ],
            )
        ])
        self.assertIn(task, saved_task.successful)
        self.assertEqual(answer, saved_task.successful[0].data[0].data)

        # Complete task
        task = await api.get_task(task.iid, task.tid)
        completed = await api.complete_tasks([
            TaskChange(
                iid=task.iid,
                tid=task.tid,
                data=[
                    TaskDataChange(
                        dataId=field.data_id,
                        data=field.data
                    )
                    for field in task.data
                ],
            )
        ])
        self.assertIn(task, completed.successful)
        workflow = api.Store.get_workflow(task.iid)
        self.assertNotIn(task, workflow.tasks)

        # Finish workflow
        await api.complete_workflow(workflow.iid)
        self.assertNotIn(workflow, await api.get_active_workflows('anon', []))

    @run_async
    @mock.patch('prism_api.rexflow.api.Store', Store)
    @mock.patch('prism_api.rexflow.api.REXFlowBridge', FakeREXFlowBridge)
    @mock.patch('prism_api.rexflow.api.get_deployments', get_deployments)
    async def test_cancel_workflow(self):
        workflow = await api.start_workflow(deployment_id=MOCK_DID)
        result = await api.cancel_workflow(workflow.iid)
        self.assertTrue(result)

        workflow = api.Store.get_workflow(workflow.iid)
        self.assertEqual(workflow.status, api.WorkflowStatus.CANCELED)
