import unittest
from unittest import mock

import pytest
from rexredis import RexRedis

from ..mocks.rexflow_entities import mock_task, mock_workflow
from prism_api.rexflow.store.errors import WorkflowNotFoundError
from prism_api.rexflow.store.redis import Store as RedisStore


REXREDIS_PATH = 'prism_api.rexflow.store.redis.Store._get_redis'


def mock_redis_client():
    return mock.MagicMock(spec=RexRedis)


@pytest.mark.ci
class TestREXFlowStore(unittest.TestCase):
    def setUp(self):
        self.mock_redis = mock_redis_client()
        self.workflow = mock_workflow()
        self.workflow_key = RedisStore.WORKFLOW_PREFIX + self.workflow.iid
        self.task = mock_task()
        self.task_key = RedisStore._get_task_key(self.task.iid, self.task.tid)

    def test_add_workflow(self):
        with mock.patch(REXREDIS_PATH, return_value=self.mock_redis):
            RedisStore.add_workflow(self.workflow)
            self.mock_redis.set_json.assert_called_with(
                self.workflow_key,
                self.workflow.dict(),
            )

    def test_get_workflow(self):
        with mock.patch(REXREDIS_PATH, return_value=self.mock_redis):
            self.mock_redis.get_from_json.return_value = None
            with self.assertRaises(WorkflowNotFoundError):
                RedisStore.get_workflow(self.workflow.iid)
            self.mock_redis.get_from_json.assert_called()

        with mock.patch(REXREDIS_PATH, return_value=self.mock_redis):
            self.mock_redis.get_from_json.return_value = self.workflow.dict()
            returned_workflow = RedisStore.get_workflow(self.workflow.iid)
            self.assertEqual(self.workflow, returned_workflow)

    def test_get_workflow_list(self):
        with mock.patch(REXREDIS_PATH, return_value=self.mock_redis):
            self.mock_redis.find_keys.side_effect = lambda x: \
                [self.workflow_key] if x == RedisStore.WORKFLOW_PREFIX else []
            self.mock_redis.get_from_json.return_value = self.workflow.dict()
            workflow_list = RedisStore.get_workflow_list()
            self.mock_redis.get_from_json.assert_called_with(self.workflow_key)
            self.assertIn(self.workflow, workflow_list)

    def test_delete_workflow(self):
        with mock.patch(REXREDIS_PATH, return_value=self.mock_redis):
            RedisStore.delete_workflow(self.workflow.iid)
            self.mock_redis.delete_keys.assert_called_with(self.workflow_key)

    def test_add_task(self):
        with mock.patch(REXREDIS_PATH, return_value=self.mock_redis):
            RedisStore.add_task(self.task)
            self.mock_redis.set_json.assert_called_with(
                self.task_key,
                self.task.dict(),
            )

    def test_update_task(self):
        with mock.patch(REXREDIS_PATH, return_value=self.mock_redis):
            self.mock_redis.exists.return_value = False
            RedisStore.update_task(self.task)
            self.mock_redis.exists.assert_called_with(self.task_key)
            self.mock_redis.set_json.assert_not_called()

            self.mock_redis.exists.return_value = True
            RedisStore.update_task(self.task)
            self.mock_redis.exists.assert_called_with(self.task_key)
            self.mock_redis.set_json.assert_called_with(
                self.task_key,
                self.task.dict(),
            )

    def test_get_workflow_tasks(self):
        with mock.patch(REXREDIS_PATH, return_value=self.mock_redis):
            self.mock_redis.find_keys.return_value = [self.task_key]
            self.mock_redis.get_from_json.return_value = self.task.dict()
            tasks_list = RedisStore.get_workflow_tasks(self.workflow.iid)
            self.assertIn(self.task.tid, tasks_list)
            self.assertEqual(self.task, tasks_list[self.task.tid])
            self.mock_redis.find_keys.assert_called_with(
                RedisStore.TASK_PREFIX + self.workflow.iid
            )
            self.mock_redis.get_from_json.assert_called_with(self.task_key)

    def test_get_task(self):
        with mock.patch(REXREDIS_PATH, return_value=self.mock_redis):
            self.mock_redis.get_from_json.return_value = self.task.dict()
            task = RedisStore.get_task(self.task.iid, self.task.tid)
            self.mock_redis.get_from_json.assert_called_with(self.task_key)
            self.assertEqual(task, self.task)

    def test_delete_task(self):
        with mock.patch(REXREDIS_PATH, return_value=self.mock_redis):
            RedisStore.delete_task(self.task.iid, self.task.tid)
            self.mock_redis.delete_keys.assert_called_with(self.task_key)
