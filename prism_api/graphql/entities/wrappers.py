"""Data wrappers for transmission"""
from typing import Dict, List, Optional

from pydantic import BaseModel

from .types import State
from prism_api.rexflow.entities.types import (
    DataId,
    OperationStatus,
    Task,
    Validator,
    Workflow,
    WorkflowInstanceId,
    WorkflowDeploymentId,
    TaskId,
)


# GraphQL filter types

class WorkflowFilter(BaseModel):
    ids: List[WorkflowInstanceId]


class TaskFilter(BaseModel):
    ids: List[TaskId] = []


# GraphQL input types

class UpdateStateInput(BaseModel):
    state: State


class StartWorkflowInput(BaseModel):
    did: WorkflowDeploymentId  # deployment id


class StartWorkflowInputBridge(BaseModel):
    did: WorkflowDeploymentId
    callback: str


class CompleteWorkflowInput(BaseModel):
    iid: WorkflowInstanceId


class TaskDataInput(BaseModel):
    dataId: DataId
    data: str


class TaskInput(BaseModel):
    iid: WorkflowInstanceId
    tid: TaskId
    data: List[TaskDataInput]


class ValidateTaskInput(BaseModel):
    tasks: List[TaskInput]


class SaveTaskInput(BaseModel):
    tasks: List[TaskInput]


class CompleteTasksInput(BaseModel):
    tasks: List[TaskInput]


# GraphQL error types

class Problem(BaseModel):
    message: str

    def resolve_type(self):
        pass


class ValidationProblem(Problem):
    iid: WorkflowInstanceId
    tid: TaskId
    dataId: DataId
    validator: Validator

    def resolve_type(self):
        return 'ValidationProblem'

    def is_type_of(self, type):
        if type == 'TaskProblems':
            return True

        return False


# GraphQL payload types

class Payload(BaseModel):
    status: OperationStatus
    errors: Optional[List[Problem]]
    query: Dict = {}


class UpdateStatePayload(Payload):
    state: State


class StartWorkflowPayload(Payload):
    iid: Optional[WorkflowInstanceId]  # instance id
    workflow: Optional[Workflow]


class CompleteWorkflowPayload(Payload):
    iid: Optional[WorkflowInstanceId]


class StartTasksPayload(Payload):
    tasks: Optional[List[Task]]


class ValidateTasksPayload(Payload):
    tasks: Optional[List[Task]]


class SaveTasksPayload(Payload):
    tasks: Optional[List[Task]]


class CompleteTaskPayload(Payload):
    tasks: Optional[List[Task]]
