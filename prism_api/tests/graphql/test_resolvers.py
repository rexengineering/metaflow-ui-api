import unittest
from unittest import mock
from typing import List

import pytest

from ..mocks import (
    MOCK_BRIDGE_URL,
    MOCK_DID,
    MOCK_IID,
    MOCK_NAME,
    MOCK_TID,
    rexflow_api,
)
from ..mocks.graphql_info import MockInfo
from ..mocks.state_store import FakeStore
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
    Problem,
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


async def mock_get_deployments():
    return [
        WorkflowDeployment(
            name=MOCK_NAME,
            deployments=[MOCK_DID],
            bridge_url=MOCK_BRIDGE_URL,
        ),
    ]


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


async def dummy_verification(*args, **kwargs):
    pass


@mock.patch(
    'prism_api.state_manager.store.api.Store',
    FakeStore,
)
@mock.patch(
    'prism_api.graphql.decorators.verify_access_token',
    dummy_verification,
)
class TestSessionResolvers(unittest.TestCase):
    @run_async
    async def test_session_resolver(self):
        response = await resolve_session(
            {},
            MockInfo(),
        )
        self.assertTrue(response)


@pytest.mark.ci
@mock.patch(
    'prism_api.graphql.resolvers.rexflow',
    rexflow_api,
)
@mock.patch(
    'prism_api.graphql.decorators.verify_access_token',
    dummy_verification,
)
class TestRexflowResolvers(unittest.TestCase):
    @run_async
    async def test_active_workflows(self):
        resolver = WorkflowResolver()
        response = await resolver.active(
            MockInfo(),
        )
        self.assertIsInstance(response, List)
        for workflow in response:
            self.assertIsInstance(workflow, Workflow)

    @run_async
    async def test_available_workflows(self):
        resolver = WorkflowResolver()
        response = await resolver.available(MockInfo())
        self.assertIsInstance(response, List)
        for workflow in response:
            self.assertIsInstance(workflow, WorkflowDeployment)

    @run_async
    async def test_start_workflow(self):
        mutations = WorkflowMutations()
        response = await mutations.start(
            MockInfo(),
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
            MockInfo(),
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
            MockInfo(),
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
            MockInfo(),
            input=CompleteTasksInput(
                tasks=[get_task_input()]
            )
        )
        self.assertIsInstance(response, CompleteTaskPayload)
        self.assertEqual(response.status, OperationStatus.SUCCESS)


@pytest.mark.ci
@mock.patch(
    'prism_api.graphql.resolvers.rexflow',
    rexflow_api,
)
@mock.patch(
    'prism_api.graphql.decorators.verify_access_token',
    dummy_verification,
)
class TestRexflowResolversErrors(unittest.TestCase):
    @run_async
    async def test_validate_tasks_errors(self):
        mutations = TasksMutations()
        response = await mutations.validate(
            MockInfo(),
            input=ValidateTaskInput(
                tasks=[],
            ),
        )
        self.assertIsInstance(response, ValidateTasksPayload)
        self.assertEqual(response.status, OperationStatus.FAILURE)
        self.assertGreater(len(response.errors), 0)
        for error in response.errors:
            self.assertIsInstance(error, Problem)

    @run_async
    async def test_save_tasks_errors(self):
        mutations = TasksMutations()
        response = await mutations.save(
            MockInfo(),
            input=SaveTaskInput(
                tasks=[],
            ),
        )
        self.assertIsInstance(response, SaveTasksPayload)
        self.assertEqual(response.status, OperationStatus.FAILURE)
        self.assertGreater(len(response.errors), 0)
        for error in response.errors:
            self.assertIsInstance(error, Problem)

    @run_async
    async def test_complete_tasks_errors(self):
        mutations = TasksMutations()
        response = await mutations.complete(
            MockInfo(),
            input=CompleteTasksInput(
                tasks=[]
            )
        )
        self.assertIsInstance(response, CompleteTaskPayload)
        self.assertEqual(response.status, OperationStatus.FAILURE)
        self.assertGreater(len(response.errors), 0)
        for error in response.errors:
            self.assertIsInstance(error, Problem)
