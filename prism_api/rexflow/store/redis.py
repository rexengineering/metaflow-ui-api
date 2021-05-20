from typing import Dict, List

from rexredis import RexRedis

from .base import StoreABC
from prism_api.rexflow.entities.types import (
    Task,
    TaskId,
    Workflow,
    WorkflowInstanceId,
)


class Store(StoreABC):
    _redis = None

    WORKFLOW_PREFIX = 'workflow:'

    TASK_PREFIX = 'task:'

    @classmethod
    def _get_redis(cls):
        if cls._redis is None or cls._redis.ping() is False:
            cls._redis = RexRedis()
        return cls._redis

    @classmethod
    def add_workflow(cls, workflow: Workflow):
        redis = cls._get_redis()
        redis.set_json(cls.WORKFLOW_PREFIX + workflow.iid, workflow.dict())

    @classmethod
    def get_workflow(cls, workflow_id: WorkflowInstanceId) -> Workflow:
        redis = cls._get_redis()
        workflow_data = redis.get_from_json(cls.WORKFLOW_PREFIX + workflow_id)
        workflow = Workflow(**workflow_data)
        tasks = cls.get_workflow_tasks(workflow_id)
        workflow.tasks = tasks.values()
        return workflow

    @classmethod
    def get_workflow_list(
        cls,
        iids: List[WorkflowInstanceId],
    ) -> List[Workflow]:
        redis = cls._get_redis()
        if len(iids) == 0:
            iids = redis.find_keys(cls.WORKFLOW_PREFIX)

        workflows = []
        for iid in iids:
            workflow = cls.get_workflow(iid)
            workflows.append(workflow)

        return workflows

    @classmethod
    def delete_workflow(cls, workflow_id: WorkflowInstanceId):
        redis = cls._get_redis()
        redis.delete_keys([workflow_id])

    @classmethod
    def _get_task_key(cls, iid: WorkflowInstanceId, tid: TaskId) -> str:
        return f'{cls.TASK_PREFIX}{iid}:{tid}'

    @classmethod
    def add_task(cls, task: Task):
        redis = cls._get_redis()
        redis.set_json(cls._get_task_key(task.iid, task.tid), task.dict())

    @classmethod
    def update_task(cls, task: Task):
        redis = cls._get_redis()
        task_key = cls._get_task_key(task.iid, task.tid)
        if redis.exists(task_key):
            redis.set_json(task_key, task.dict())

    @classmethod
    def get_workflow_tasks(
        cls,
        workflow_id: WorkflowInstanceId,
    ) -> Dict[TaskId, Task]:
        redis = cls._get_redis()
        task_keys = redis.find_keys(cls.TASK_PREFIX + workflow_id)
        tasks = {}
        for task_key in task_keys:
            task_data = redis.get_from_json(task_key)
            task = Task(**task_data)
            tasks[task.tid] = task
        return tasks

    @classmethod
    def get_task(
        cls,
        workflow_id: WorkflowInstanceId,
        task_id: TaskId,
    ) -> Task:
        task_key = cls._get_task_key(workflow_id, task_id)
        redis = cls._get_redis()
        task_data = redis.get_from_json(task_key)
        return Task(**task_data)

    @classmethod
    def delete_task(
        cls,
        workflow_id: WorkflowInstanceId,
        task_id: TaskId,
    ) -> None:
        task_key = cls._get_task_key(workflow_id, task_id)
        redis = cls._get_redis()
        redis.delete_keys([task_key])
