import unittest

import pytest

from prism_api.rexflow import api


@pytest.mark.ci
class TestWorkflow(unittest.TestCase):
    def test_happy_workflow(self):
        context = {
            'client_id': '123',
        }

        # Instance a new workflow
        workflow = api.get_workflow(context)
        self.assertIsNotNone(workflow)

        # Get current workflow task
        # Consider what to do when there is no task available
        task = workflow.get_task()
        self.assertIsNotNone(task)

        # Get task form
        form = task.get_form()
        self.assertIsNotNone(form)

        # Answer all questions
        for field in form.fields:
            field.answer = 'this is the answer'

        # Save the form
        task.save_form(form)

        # Complete task
        task.complete()

        # Finish workflow
        workflow.finish()
