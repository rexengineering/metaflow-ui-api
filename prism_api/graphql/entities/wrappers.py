"""Data wrappers for transmission"""
from typing import Dict, List, Optional

from pydantic import BaseModel

from prism_api.rexflow.entities import types as e


# GraphQL filter types

class WorkflowFilter(BaseModel):
    ids: List[e.WorkflowInstanceId]


class TaskFilter(BaseModel):
    ids: List[e.TaskId] = []


# GraphQL input types

class StartWorkflowInput(BaseModel):
    did: e.WorkflowDeploymentId  # deployment id


class StartWorkflowInputBridge(BaseModel):
    did: e.WorkflowDeploymentId
    callback: str


class CompleteWorkflowInput(BaseModel):
    iid: e.WorkflowInstanceId


class TaskDataInput(BaseModel):
    id: e.DataId
    data: str


class TaskInput(BaseModel):
    iid: e.WorkflowInstanceId
    tid: e.TaskId
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


# GraphQL payload types

class Payload(BaseModel):
    status: e.OperationStatus
    errors: Optional[List[Problem]]
    query: Dict = {}


class StartWorkflowPayload(Payload):
    iid: Optional[e.WorkflowInstanceId]  # instance id
    workflow: Optional[e.Workflow]


class CompleteWorkflowPayload(Payload):
    iid: Optional[e.WorkflowInstanceId]


class StartTasksPayload(Payload):
    tasks: Optional[List[e.Task]]


class ValidateTasksPayload(Payload):
    tasks: Optional[List[e.Task]]


class SaveTasksPayload(Payload):
    tasks: Optional[List[e.Task]]


class CompleteTaskPayload(Payload):
    tasks: Optional[List[e.Task]]
