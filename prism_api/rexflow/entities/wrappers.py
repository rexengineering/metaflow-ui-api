from typing import List, Optional

from pydantic import BaseModel

from .types import (
    DataId,
    ErrorDetails,
    OperationStatus,
    TaskFieldData,
    TaskId,
    Task,
    WorkflowDeploymentId,
    WorkflowInstanceId,
    WorkflowInstanceInfo,
    WorkflowStatus,
)


class TaskDataChange(BaseModel):
    dataId: DataId
    data: str


class TaskChange(BaseModel):
    iid: WorkflowInstanceId
    tid: TaskId
    data: List[TaskDataChange]


class TaskOperationResults(BaseModel):
    successful: List[Task] = []
    errors: List[ErrorDetails] = []


# GraphQL input types

class MetaDataInput(BaseModel):
    key: str
    value: str


class GetInstanceInput(BaseModel):
    iid: Optional[WorkflowInstanceId]
    meta_data: Optional[List[MetaDataInput]]


class CreateWorkflowInstanceInput(BaseModel):
    did: Optional[str]
    graphqlUri: str
    meta_data: Optional[List[MetaDataInput]]


class CancelWorkflowInstanceInput(BaseModel):
    iid: WorkflowInstanceId


class TaskMutationFormInput(BaseModel):
    iid: WorkflowInstanceId
    tid: TaskId
    reset: bool = False


class TaskFieldInput(BaseModel):
    dataId: DataId
    data: Optional[str]


class TaskMutationValidateInput(BaseModel):
    iid: WorkflowInstanceId
    tid: TaskId
    fields: List[TaskFieldInput]


class TaskMutationSaveInput(BaseModel):
    iid: WorkflowInstanceId
    tid: TaskId
    fields: List[TaskFieldInput]


class TaskMutationCompleteInput(BaseModel):
    iid: WorkflowInstanceId
    tid: TaskId


# GraphQL payload types

class Payload(BaseModel):
    status: OperationStatus


class CreateInstancePayload(Payload):
    did: WorkflowDeploymentId
    iid: WorkflowInstanceId
    status: OperationStatus
    tasks: List[TaskId]


class CancelInstancePayload(Payload):
    did: WorkflowDeploymentId
    iid: WorkflowInstanceId
    iid_status: WorkflowStatus


class GetInstancePayload(BaseModel):
    did: WorkflowInstanceId
    iid_list: List[WorkflowInstanceInfo]


class TaskFormPayload(Payload):
    iid: WorkflowInstanceId
    tid: TaskId
    fields: List[TaskFieldData]


class ValidatorResults(BaseModel):
    passed: bool
    message: Optional[str]


class FieldValidationResult(BaseModel):
    dataId: DataId
    passed: bool
    results: List[ValidatorResults]


class ValidatedPayload(Payload):
    iid: WorkflowInstanceId
    tid: TaskId
    passed: bool
    results: List[FieldValidationResult]


class TaskValidatePayload(ValidatedPayload):
    pass


class TaskSavePayload(ValidatedPayload):
    pass


class TaskCompletePayload(Payload):
    iid: WorkflowInstanceId
    tid: TaskId
