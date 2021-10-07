"""Data wrappers for transmission"""
from typing import Dict, List, Optional

from pydantic import BaseModel

from rexflow_ui.entities.types import (
    DataId,
    OperationStatus,
    Task,
    Validator,
    Workflow,
    WorkflowInstanceId,
    WorkflowDeploymentId,
    TaskId,
)
from rexflow_ui.events.entities import Event
from prism_api.state_manager.entities import State


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


class StartWorkflowByNameInput(BaseModel):
    name: str


class StartWorkflowInputBridge(BaseModel):
    did: WorkflowDeploymentId
    callback: str


class CompleteWorkflowInput(BaseModel):
    iid: WorkflowInstanceId


class CancelWorkflowInput(BaseModel):
    iid: List[WorkflowInstanceId]


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


class GenericProblem(Problem):
    def resolve_type(self):
        return 'GenericProblem'


class ValidationProblem(Problem):
    iid: WorkflowInstanceId
    tid: TaskId
    dataId: DataId
    validator: Validator

    def resolve_type(self):
        return 'ValidationProblem'


class ServiceNotAvailableProblem(Problem):
    def resolve_type(self):
        return 'ServiceNotAvailableProblem'


# GraphQL payload types

class KeepAlivePayload(BaseModel):
    status: OperationStatus


class EventData(BaseModel):
    workflow: Optional[Workflow]
    task: Optional[Task]


class EventBroadcastPayload(BaseModel):
    event: Event
    data: Optional[EventData]


class Payload(BaseModel):
    status: OperationStatus
    errors: Optional[List[Problem]]
    query: Dict = {}


class UpdateStatePayload(Payload):
    state: State


class StartWorkflowPayload(Payload):
    iid: Optional[WorkflowInstanceId]  # instance id
    workflow: Optional[Workflow]


class StartWorkflowByNamePayload(Payload):
    did: Optional[WorkflowDeploymentId]
    iid: Optional[WorkflowInstanceId]
    workflow: Optional[Workflow]


class CompleteWorkflowPayload(Payload):
    iid: Optional[WorkflowInstanceId]


class CancelWorkflowPayload(Payload):
    iid: Optional[List[WorkflowInstanceId]]


class StartTasksPayload(Payload):
    tasks: Optional[List[Task]]


class ValidateTasksPayload(Payload):
    tasks: Optional[List[Task]]


class SaveTasksPayload(Payload):
    tasks: Optional[List[Task]]


class CompleteTaskPayload(Payload):
    tasks: Optional[List[Task]]
