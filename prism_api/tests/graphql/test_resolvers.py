import unittest
from unittest import mock
from typing import List

import pytest

from ..mocks import (
    MOCK_DID,
    MOCK_IID,
    MOCK_TID,
    rexflow_api,
)
from ..utils import run_async
from prism_api.graphql.resolvers import (
    resolve_session,
    WorkflowResolver,
    WorkflowMutations,
    TasksMutations,
)
from prism_api.graphql.entities.wrappers import (
    CompleteTaskPayload,
    CompleteTasksInput,
    SaveTaskInput,
    SaveTasksPayload,
    StartWorkflowInput,
    StartWorkflowPayload,
    TaskDataInput,
    TaskInput,
    ValidateTaskInput,
    ValidateTasksPayload,
)
from prism_api.rexflow.entities.types import (
    OperationStatus,
    Workflow,
    WorkflowDeployment,
)


def mock_info():
    return {}


async def mock_get_deployments():
    return {
        'test_workflow': [
            MOCK_DID,
        ]
    }


def get_task_input():
    return TaskInput(
        iid=MOCK_IID,
        tid=MOCK_TID,
        data=[
            TaskDataInput(
                dataId='uname',
                data='test',
            ),
        ],
    )


class TestSessionResolvers(unittest.TestCase):
    @run_async
    async def test_session_resolver(self):
        response = await resolve_session()
        self.assertTrue(response)


@pytest.mark.ci
@mock.patch(
    'prism_api.graphql.resolvers.rexflow',
    rexflow_api,
)
class TestRexflowResolvers(unittest.TestCase):
    @run_async
    async def test_active_workflows(self):
        resolver = WorkflowResolver()
        response = await resolver.active(
            mock_info(),
        )
        self.assertIsInstance(response, List)
        for workflow in response:
            self.assertIsInstance(workflow, Workflow)

    @run_async
    async def test_available_workflows(self):
        resolver = WorkflowResolver()
        response = await resolver.available()
        self.assertIsInstance(response, List)
        for workflow in response:
            self.assertIsInstance(workflow, WorkflowDeployment)

    @run_async
    async def test_start_workflow(self):
        mutations = WorkflowMutations()
        response = await mutations.start(
            mock_info(),
            input=StartWorkflowInput(
                did=MOCK_DID,
            )
        )
        self.assertIsInstance(response, StartWorkflowPayload)
        self.assertEqual(response.status, OperationStatus.SUCCESS)

    @run_async
    async def test_validate_tasks(self):
        mutations = TasksMutations()
        response = await mutations.validate(
            mock_info(),
            input=ValidateTaskInput(
                tasks=[
                    get_task_input(),
                ],
            ),
        )
        self.assertIsInstance(response, ValidateTasksPayload)
        self.assertEqual(response.status, OperationStatus.SUCCESS)

    @run_async
    async def test_save_tasks(self):
        mutations = TasksMutations()
        response = await mutations.save(
            mock_info(),
            input=SaveTaskInput(
                tasks=[
                    get_task_input(),
                ],
            ),
        )
        self.assertIsInstance(response, SaveTasksPayload)
        self.assertEqual(response.status, OperationStatus.SUCCESS)

    @run_async
    async def test_complete_tasks(self):
        mutations = TasksMutations()
        response = await mutations.complete(
            mock_info(),
            input=CompleteTasksInput(
                tasks=[get_task_input()]
            )
        )
        self.assertIsInstance(response, CompleteTaskPayload)
        self.assertEqual(response.status, OperationStatus.SUCCESS)
