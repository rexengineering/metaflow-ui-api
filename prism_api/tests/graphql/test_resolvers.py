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
)
from ..mocks.graphql_info import MockInfo
from ..mocks.state_store import FakeStore
from ..utils import run_async
from prism_api.graphql.resolvers import (
    TalkTrackResolver,
    resolve_session,
    WorkflowResolver,
    WorkflowMutations,
    TasksMutations,
    resolve_workflow_tasks,
)
from prism_api.graphql.entities.wrappers import (
    CancelWorkflowInput,
    CancelWorkflowPayload,
    CompleteTaskPayload,
    CompleteTasksInput,
    Problem,
    SaveTaskInput,
    SaveTasksPayload,
    StartWorkflowByNameInput,
    StartWorkflowByNamePayload,
    StartWorkflowInput,
    StartWorkflowPayload,
    TaskDataInput,
    TaskFilter,
    TaskInput,
    ValidateTaskInput,
    ValidateTasksPayload,
)
from rexflow_ui.entities.types import (
    OperationStatus,
    Workflow,
    WorkflowDeployment,
)
from rexflow_ui.tests.mocks import rexflow_api
from rexflow_ui.tests.mocks.rexflow_entities import mock_workflow


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
    'prism_api.graphql.decorators._verify_access_token',
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
    'prism_api.graphql.decorators._verify_access_token',
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
        self.assertGreater(len(response), 0)
        for workflow in response:
            self.assertIsInstance(workflow, WorkflowDeployment)

    @run_async
    async def test_workflow_deployments(self):
        resolver = WorkflowResolver()
        response = await resolver.deployments(MockInfo())
        self.assertIsInstance(response, List)
        self.assertGreater(len(response), 0)
        for workflow_id in response:
            self.assertIsInstance(workflow_id, str)

    @run_async
    async def test_workflow_directory(self):
        resolver = WorkflowResolver()
        response = await resolver.directory(MockInfo())
        self.assertIsInstance(response, dict)
        self.assertGreater(len(response), 0)
        for workflow_id in response.values():
            self.assertIsInstance(workflow_id, str)

    @run_async
    async def test_workflow_tasks(self):
        task_number = 5
        workflow = mock_workflow(task_number=task_number)
        for task in workflow.tasks:
            result = await resolve_workflow_tasks(
                workflow,
                MockInfo(),
                TaskFilter(ids=[task.tid]),
            )
            self.assertEqual(1, len(result))
            self.assertIn(task, result)
        result = await resolve_workflow_tasks(workflow, MockInfo())
        self.assertEqual(result, workflow.tasks)
        self.assertEqual(task_number, len(result))

    @run_async
    async def test_talktracks_list(self):
        resolver = TalkTrackResolver()
        with mock.patch(
            'prism_api.graphql.resolvers.settings.TALKTRACK_WORKFLOWS',
            [],
        ):
            talktracks = await resolver.list(MockInfo())
        self.assertEqual(len(talktracks), 0)

        with mock.patch(
            'prism_api.graphql.resolvers.settings.TALKTRACK_WORKFLOWS',
            [MOCK_NAME],
        ):
            talktracks = await resolver.list(MockInfo())
        self.assertEqual(len(talktracks), 1)

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
    async def test_start_workflow_by_name(self):
        mutations = WorkflowMutations()
        response = await mutations.start_by_name(
            MockInfo(),
            input=StartWorkflowByNameInput(
                name=MOCK_NAME,
            )
        )
        self.assertIsInstance(response, StartWorkflowByNamePayload)
        self.assertEqual(response.status, OperationStatus.SUCCESS)

    @run_async
    async def test_cancel_workflow(self):
        mutations = WorkflowMutations()
        response = await mutations.cancel(
            MockInfo(),
            input=CancelWorkflowInput(
                iid=[MOCK_IID],
            ),
        )
        self.assertIsInstance(response, CancelWorkflowPayload)
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
    'prism_api.graphql.decorators._verify_access_token',
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
