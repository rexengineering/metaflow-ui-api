from . import (
    MOCK_BRIDGE_URL,
    MOCK_DATA_ID,
    MOCK_DATA_ID_BASE,
    MOCK_DID,
    MOCK_IID,
    MOCK_NAME,
    MOCK_TID,
    MOCK_TID_BASE,
)
from prism_api.rexflow.entities.types import (
    WorkflowStatus,
    TaskStatus,
    ValidatorEnum,
    DataType,
    Validator,
    TaskFieldData,
    Task,
    Workflow,
)
from prism_api.rexflow.entities.wrappers import TaskChange, TaskDataChange


def mock_task_field_data(
    *,
    field_number=0,
    dataId: str = MOCK_DATA_ID_BASE,
    field_type=DataType.TEXT,
    field_label='test',
    field_data='',
    included_validators: list[Validator] = None,
):
    if included_validators is None:
        validators = [Validator(
            type=ValidatorEnum.REGEX,
            constraint=r'^.*$',
        )]
    else:
        # included validators may be an empty list
        validators = included_validators
    return TaskFieldData(
        dataId=dataId.format(n=field_number),
        type=field_type,
        order=field_number,
        label=field_label,
        data=field_data,
        validators=validators,
    )


def mock_task(
    *,
    task_number=0,
    iid=MOCK_IID,
    tid: str = MOCK_TID_BASE,
    task_status=TaskStatus.UP,
    field_number=1,
    **mock_info,
):
    return Task(
        iid=iid,
        tid=tid.format(n=task_number),
        data=[
            mock_task_field_data(
                field_number=i,
                **mock_info,
            )
            for i in range(field_number)
        ],
        status=task_status,
    )


def mock_workflow(
    *,
    iid=MOCK_IID,
    did=MOCK_DID,
    name=MOCK_NAME,
    workflow_status=WorkflowStatus.RUNNING,
    task_number=0,
    **mock_info,
):
    return Workflow(
        iid=iid,
        did=did,
        name=name,
        status=workflow_status,
        tasks=[
            mock_task(
                task_number=i,
                iid=iid,
                **mock_info,
            )
            for i in range(task_number)
        ],
        bridge_url=MOCK_BRIDGE_URL,
    )


def mock_task_change():
    return TaskChange(
        iid=MOCK_IID,
        tid=MOCK_TID,
        data=[TaskDataChange(
            dataId=MOCK_DATA_ID,
            data='test',
        )]
    )
