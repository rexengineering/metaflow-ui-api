import unittest
from unittest import mock

import pytest

from ..utils import FakeREXFlowBridge, run_async
from prism_api.rexflow import api
from prism_api.rexflow.entities import types as e


FakeREXFlowBridge.sleep_time = 0.1


@pytest.mark.ci
class TestWorkflow(unittest.TestCase):
    @run_async
    @mock.patch('prism_api.rexflow.api.REXFlowBridge', FakeREXFlowBridge)
    async def test_happy_workflow(self):
        # Instance a new workflow
        workflow = await api.start_workflow(deployment_id='123')
        self.assertIsNotNone(workflow)
        self.assertEqual(len(workflow.tasks), 0)
        self.assertIn(workflow, await api.get_active_workflows())

        new_task = e.Task(
            iid=workflow.iid,
            tid='t123',
            data=[
                e.TaskFieldData(
                    id='fname',
                    type=e.DataType.TEXT,
                    order=1,
                    label='First Name',
                    validators=[
                        e.Validator(
                            type=e.ValidatorEnum.REGEX,
                            constraint=r'.*'
                        )
                    ]
                )
            ]
        )

        created = await api.start_tasks([new_task])
        self.assertIn(new_task, created)
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

        # Save the form
        saved_task = await api.save_tasks([task])
        self.assertIn(task, saved_task)
        self.assertEqual(answer, saved_task[0].data[0].data)

        # Complete task
        completed = await api.complete_tasks([task])
        task = await api.get_task(task.iid, task.tid)
        self.assertIn(task, completed)
        self.assertEqual(task.status, e.TaskStatus.DOWN)

        # Finish workflow
        await api.complete_workflow(workflow.iid)
        self.assertNotIn(workflow, await api.get_active_workflows())
