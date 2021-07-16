from typing import List

from pydantic import validate_arguments

from ..mocks import MOCK_DID, MOCK_IID, MOCK_TID
from prism_api.graphql.entities.types import SessionId
from prism_api.rexflow.entities.types import (
    MetaData,
    Task,
    TaskFieldData,
    TaskId,
    Workflow,
    WorkflowDeployment,
    WorkflowDeploymentId,
    WorkflowInstanceId,
    WorkflowStatus
)
from prism_api.rexflow.entities.wrappers import (
    TaskChange,
    TaskOperationResults,
)


def _mock_task():
    return Task(
        iid=MOCK_IID,
        tid=MOCK_TID,
        data=[
            TaskFieldData(
                dataId='uname',
                type='TEXT',
                order=1,
            ),
        ],
    )


def _mock_workflow(with_tasks=True):
    if with_tasks:
        tasks = [
            _mock_task(),
        ]
    else:
        tasks = []

    return Workflow(
        did=MOCK_DID,
        iid=MOCK_IID,
        status=WorkflowStatus.RUNNING,
        tasks=tasks,
    )


async def get_available_workflows() -> List[WorkflowDeployment]:
    return [
        WorkflowDeployment(
            name='test_workflow',
            deployments=[MOCK_DID]
        )
    ]


async def start_workflow(
    deployment_id: WorkflowDeploymentId,
    metadata: List[MetaData] = [],
) -> Workflow:
    return _mock_workflow(with_tasks=False)


@validate_arguments
async def get_active_workflows(
    session_id: SessionId,
    iids: List[WorkflowInstanceId]
) -> List[Workflow]:
    return [_mock_workflow()]


async def complete_workflow(instance_id: WorkflowInstanceId) -> None:
    pass


@validate_arguments
async def start_tasks(
    iid: WorkflowInstanceId,
    tasks: List[TaskId]
) -> List[Task]:
    return [
        Task(
            iid=iid,
            tid=tid,
        )
        for tid in tasks
    ]


@validate_arguments
async def get_task(iid: WorkflowInstanceId, tid: TaskId) -> Task:
    return _mock_task()


@validate_arguments
async def validate_tasks(tasks: List[TaskChange]) -> TaskOperationResults:
    result = TaskOperationResults()
    result.successful = [_mock_task()]
    return result


@validate_arguments
async def save_tasks(tasks: List[TaskChange]) -> TaskOperationResults:
    result = TaskOperationResults()
    result.successful = [_mock_task()]
    return result


@validate_arguments
async def complete_tasks(tasks: List[TaskChange]) -> TaskOperationResults:
    result = TaskOperationResults()
    result.successful = [_mock_task()]
    return result
