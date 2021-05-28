import unittest
from unittest import mock

import pytest

from ..mocks import MOCK_DID, MOCK_TID
from ..mocks.rexflow_bridge import FakeREXFlowBridge
from ..utils import run_async
from prism_api.rexflow import api


FakeREXFlowBridge.sleep_time = 0.1


async def get_deployments():
    return {
        'test': [
            MOCK_DID,
        ]
    }


@pytest.mark.ci
class TestWorkflow(unittest.TestCase):
    @run_async
    @mock.patch('prism_api.rexflow.api.REXFlowBridge', FakeREXFlowBridge)
    @mock.patch('prism_api.rexflow.api.get_deployments', get_deployments)
    async def test_happy_workflow(self):
        # Instance a new workflow
        workflow = await api.start_workflow(deployment_id=MOCK_DID)
        self.assertIsNotNone(workflow)
        self.assertEqual(len(workflow.tasks), 0)
        self.assertIn(workflow, await api.get_active_workflows([]))

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
        validated_tasks = await api.validate_tasks([task])
        self.assertIn(task, validated_tasks.successful)
        self.assertEqual(answer, validated_tasks.successful[0].data[0].data)

        # Save the form
        saved_task = await api.save_tasks([task])
        self.assertIn(task, saved_task.successful)
        self.assertEqual(answer, saved_task.successful[0].data[0].data)

        # Complete task
        task = await api.get_task(task.iid, task.tid)
        completed = await api.complete_tasks([task])
        self.assertIn(task, completed.successful)
        workflow = api.Store.get_workflow(task.iid)
        self.assertNotIn(task, workflow.tasks)

        # Finish workflow
        await api.complete_workflow(workflow.iid)
        self.assertNotIn(workflow, api.Store.get_workflow_list([]))
