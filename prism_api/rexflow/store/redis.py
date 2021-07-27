import logging
from typing import Dict, List

from rexredis import RexRedis

from .base import StoreABC
from .errors import (
    WorkflowNotFoundError,
    TaskNotFoundError,
)
from prism_api.rexflow.entities.types import (
    Task,
    TaskId,
    Workflow,
    WorkflowDeployment,
    WorkflowInstanceId,
)

logger = logging.getLogger(__name__)


class Store(StoreABC):
    _redis = None

    DEPLOYMENT_KEY = 'rexflow:deployments'

    WORKFLOW_PREFIX = 'workflow:'

    TASK_PREFIX = 'task:'

    @classmethod
    def _get_redis(cls):
        if cls._redis is None or cls._redis.ping() is False:
            cls._redis = RexRedis()
        return cls._redis

    @classmethod
    def save_deployments(cls, deployments: List[WorkflowDeployment]):
        redis = cls._get_redis()
        redis.set_json(
            cls.DEPLOYMENT_KEY,
            [deployment.dict() for deployment in deployments],
        )

    @classmethod
    def get_deployments(cls) -> List[WorkflowDeployment]:
        redis = cls._get_redis()
        deployments = redis.get_from_json(cls.DEPLOYMENT_KEY)
        if deployments:
            return [
                WorkflowDeployment(**deployment)
                for deployment in deployments
            ]
        else:
            return []

    @classmethod
    def add_workflow(cls, workflow: Workflow):
        redis = cls._get_redis()
        redis.set_json(cls.WORKFLOW_PREFIX + workflow.iid, workflow.dict())

    @classmethod
    def _get_workflow(cls, workflow_key):
        redis = cls._get_redis()
        workflow_data = redis.get_from_json(workflow_key)
        if workflow_data:
            workflow = Workflow(**workflow_data)
        else:
            raise WorkflowNotFoundError
        tasks = cls.get_workflow_tasks(workflow.iid)
        workflow.tasks = list(tasks.values())
        return workflow

    @classmethod
    def get_workflow(cls, workflow_id: WorkflowInstanceId) -> Workflow:
        workflow = cls._get_workflow(cls.WORKFLOW_PREFIX + workflow_id)
        return workflow

    @classmethod
    def get_workflow_list(
        cls,
        iids: List[WorkflowInstanceId] = [],
    ) -> List[Workflow]:
        if len(iids) == 0:
            redis = cls._get_redis()
            workflow_keys = redis.find_keys(cls.WORKFLOW_PREFIX)
        else:
            workflow_keys = [
                cls.WORKFLOW_PREFIX + iid
                for iid in iids
            ]

        workflows = []
        for workflow_key in workflow_keys:
            try:
                workflow = cls._get_workflow(workflow_key)
            except WorkflowNotFoundError:
                logger.exception(f'Data for {workflow_key} not found')
            else:
                workflows.append(workflow)

        return workflows

    @classmethod
    def delete_workflow(cls, workflow_id: WorkflowInstanceId):
        workflow_key = cls.WORKFLOW_PREFIX + workflow_id
        redis = cls._get_redis()
        redis.delete_keys(workflow_key)

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
        if not redis.exists(cls.WORKFLOW_PREFIX + workflow_id):
            raise WorkflowNotFoundError
        task_keys = redis.find_keys(cls.TASK_PREFIX + workflow_id)
        tasks = {}
        for task_key in task_keys:
            task_data = redis.get_from_json(task_key)
            if task_data:
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
        if task_data is None:
            raise TaskNotFoundError
        return Task(**task_data)

    @classmethod
    def delete_task(
        cls,
        workflow_id: WorkflowInstanceId,
        task_id: TaskId,
    ) -> None:
        redis = cls._get_redis()
        if not redis.exists(cls.WORKFLOW_PREFIX + workflow_id):
            raise WorkflowNotFoundError
        task_key = cls._get_task_key(workflow_id, task_id)
        redis.delete_keys(task_key)
