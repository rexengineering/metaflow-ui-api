from typing import List, Optional

from pydantic import BaseModel

from . import types as e


class TaskDataChange(BaseModel):
    dataId: e.DataId
    data: str


class TaskChange(BaseModel):
    iid: e.WorkflowInstanceId
    tid: e.TaskId
    data: List[TaskDataChange]


# GraphQL input types

class CreateWorkflowInstanceInput(BaseModel):
    graphqlUri: str


class TaskMutationFormInput(BaseModel):
    iid: e.WorkflowInstanceId
    tid: e.TaskId


class TaskFieldInput(BaseModel):
    dataId: e.DataId
    type: e.DataType
    data: Optional[str]
    encrypted: bool


class TaskMutationValidateInput(BaseModel):
    iid: e.WorkflowInstanceId
    tid: e.TaskId
    fields: List[TaskFieldInput]


class TaskMutationSaveInput(BaseModel):
    iid: e.WorkflowInstanceId
    tid: e.TaskId
    fields: List[TaskFieldInput]


class TaskMutationCompleteInput(BaseModel):
    iid: e.WorkflowInstanceId
    tid: e.TaskId


# GraphQL payload types

class Payload(BaseModel):
    status: e.OperationStatus


class CreateInstancePayload(Payload):
    did: e.WorkflowDeploymentId
    iid: e.WorkflowInstanceId
    status: e.OperationStatus
    tasks: List[e.TaskId]


class GetInstancePayload(BaseModel):
    did: e.WorkflowInstanceId
    iid_list: List[e.WorkflowInstanceInfo]


class TaskFormPayload(Payload):
    iid: e.WorkflowInstanceId
    tid: e.TaskId
    fields: List[e.TaskFieldData]


class ValidatorResults(BaseModel):
    validator: e.Validator
    passed: bool
    result: Optional[str]


class FieldValidationResult(BaseModel):
    dataId: e.DataId
    passed: bool
    result: Optional[ValidatorResults]


class TaskValidatePayload(Payload):
    iid: e.WorkflowInstanceId
    tid: e.TaskId
    passed: bool
    results: List[FieldValidationResult]


class TaskSavePayload(Payload):
    iid: e.WorkflowInstanceId
    tid: e.TaskId
    passed: bool
    results: List[FieldValidationResult]


class TaskCompletePayload(Payload):
    iid: e.WorkflowInstanceId
    tid: e.TaskId
