import unittest
from unittest import mock

import pytest

from ..mocks import (
    MOCK_IID,
    MOCK_TID,
    MOCK_XID,
)
from ..mocks.graphql_info import MockInfo
from ..utils import run_async
from prism_api.callback.resolvers import (
    TaskMutations as TaskCallbackMutations,
    WorkflowMutations as WorkflowCallbackMutations,
)
from prism_api.callback.entities import (
    CompleteWorkflowInput,
    CompleteWorkflowPayload,
    StartTaskInput,
    StartTaskPayload,
)
from rexflow_ui.entities.types import (
    OperationStatus,
)
from rexflow_ui.errors import BridgeNotReachableError
from rexflow_ui.tests.mocks import rexflow_api


def _raise_bridge_exception(*_, **__):
    raise BridgeNotReachableError('test')


def _raise_exception(*_, **__):
    raise Exception('test')


@pytest.mark.ci
@mock.patch(
    'prism_api.callback.resolvers.api',
    rexflow_api,
)
class TestCallBackResolvers(unittest.TestCase):
    @run_async
    async def test_start_task_callback(self):
        mutations = TaskCallbackMutations()
        response = await mutations.start(
            MockInfo(),
            input=StartTaskInput(
                iid=MOCK_IID,
                tid=MOCK_TID,
            ),
        )
        self.assertIsInstance(response, StartTaskPayload)
        self.assertEqual(response.status, OperationStatus.SUCCESS)

    @run_async
    async def test_tast_task_exchange_callback(self):
        mutations = TaskCallbackMutations()
        response = await mutations.start(
            MockInfo(),
            input=StartTaskInput(
                iid=MOCK_IID,
                tid=MOCK_TID,
                xid=MOCK_XID,
            )
        )
        self.assertIsInstance(response, StartTaskPayload)
        self.assertEqual(response.status, OperationStatus.SUCCESS)

    @run_async
    async def test_complete_workflow_callback(self):
        mutations = WorkflowCallbackMutations()
        response = await mutations.complete(
            MockInfo(),
            input=CompleteWorkflowInput(
                iid=MOCK_IID,
            ),
        )
        self.assertIsInstance(response, CompleteWorkflowPayload)
        self.assertEqual(response.status, OperationStatus.SUCCESS)


@pytest.mark.ci
class TestCallBackResolversErrors(unittest.TestCase):
    @run_async
    async def test_start_task_mutation_errors(self):
        mutations = TaskCallbackMutations()
        with mock.patch(
            'prism_api.callback.resolvers.api.start_tasks',
        ) as call:
            call.side_effect = _raise_bridge_exception
            response = await mutations.start(
                MockInfo(),
                input=StartTaskInput(
                    iid=MOCK_IID,
                    tid=MOCK_TID,
                ),
            )

        self.assertIsInstance(response, StartTaskPayload)
        self.assertEqual(response.status, OperationStatus.FAILURE)

        with mock.patch(
            'prism_api.callback.resolvers.api.start_tasks',
        ) as call:
            call.side_effect = _raise_exception
            response = await mutations.start(
                MockInfo(),
                input=StartTaskInput(
                    iid=MOCK_IID,
                    tid=MOCK_TID,
                ),
            )

        self.assertIsInstance(response, StartTaskPayload)
        self.assertEqual(response.status, OperationStatus.FAILURE)

    @run_async
    async def test_complete_workflow_callback_errors(self):
        mutations = WorkflowCallbackMutations()
        with mock.patch(
            'prism_api.callback.resolvers.api.complete_workflow',
        ) as call:
            call.side_effect = _raise_exception
            response = await mutations.complete(
                MockInfo(),
                input=CompleteWorkflowInput(
                    iid=MOCK_IID,
                ),
            )
        self.assertIsInstance(response, CompleteWorkflowPayload)
        self.assertEqual(response.status, OperationStatus.FAILURE)
