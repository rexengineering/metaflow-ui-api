from typing import List

from pydantic import validate_arguments

from ..mocks import (
    MOCK_DATA_ID,
    MOCK_DID,
    MOCK_IID,
    MOCK_NAME,
    MOCK_TID,
)
from rexflow_ui.entities.types import (
    ErrorDetails,
    MetaData,
    OperationStatus,
    Task,
    TaskFieldData,
    TaskId,
    Workflow,
    WorkflowDeployment,
    WorkflowDeploymentId,
    WorkflowInstanceId,
    WorkflowStatus
)
from rexflow_ui.entities.wrappers import (
    FieldValidationResult,
    TaskChange,
    TaskOperationResults,
    ValidatedPayload,
    ValidatorResults,
)
from rexflow_ui.errors import ValidationErrorDetails
from prism_api.state_manager.entities import SessionId


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


def _mock_validation_error():
    return ValidationErrorDetails.init_from_payload(
        payload=ValidatedPayload(
            iid=MOCK_IID,
            tid=MOCK_TID,
            passed=False,
            results=[
                FieldValidationResult(
                    dataId=MOCK_DATA_ID,
                    passed=False,
                    results=[
                        ValidatorResults(
                            passed=False,
                            message='test failed validation',
                        ),
                    ],
                ),
            ],
            status=OperationStatus.FAILURE,
        ),
    )


def _mock_error():
    return ErrorDetails(message='test error')


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


async def get_available_workflows(refresh=False) -> List[WorkflowDeployment]:
    return [
        WorkflowDeployment(
            name=MOCK_NAME,
            deployments=[MOCK_DID],
            bridge_url='',
        )
    ]


async def start_workflow(
    deployment_id: WorkflowDeploymentId,
    metadata: List[MetaData] = [],
) -> Workflow:
    return _mock_workflow(with_tasks=False)


async def start_workflow_by_name(
    workflow_name: str,
    metadata: List[MetaData] = [],
) -> Workflow:
    return _mock_workflow(with_tasks=False)


async def refresh_workflows():
    pass


@validate_arguments
async def get_active_workflows(
    session_id: SessionId,
    iids: List[WorkflowInstanceId]
) -> List[Workflow]:
    return [_mock_workflow()]


async def complete_workflow(instance_id: WorkflowInstanceId) -> None:
    pass


async def cancel_workflow(
    instance_id: WorkflowInstanceId,
) -> bool:
    return True


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
    if tasks:
        result.successful = [_mock_task()]
    else:
        result.errors = [_mock_validation_error(), _mock_error()]

    return result


@validate_arguments
async def save_tasks(tasks: List[TaskChange]) -> TaskOperationResults:
    result = TaskOperationResults()
    if tasks:
        result.successful = [_mock_task()]
    else:
        result.errors = [_mock_validation_error(), _mock_error()]

    return result


@validate_arguments
async def complete_tasks(tasks: List[TaskChange]) -> TaskOperationResults:
    result = TaskOperationResults()
    if tasks:
        result.successful = [_mock_task()]
    else:
        result.errors = [_mock_validation_error(), _mock_error()]

    return result
