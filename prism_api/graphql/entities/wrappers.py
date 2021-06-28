"""Data wrappers for transmission"""
from typing import Dict, List, Optional

from pydantic import BaseModel
from pydantic.types import UUID4

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
from prism_api.talktrack.entities import (
    TalkTrackId,
    TalkTrack,
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


class StartTalkTrackInput(BaseModel):
    talktrack_id: List[TalkTrackId]


class ActivateTalkTrackInput(BaseModel):
    talktrack_uuid: UUID4


class FinishTalkTrackInput(BaseModel):
    talktrack_uuid: List[UUID4]


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


class StartTalkTrackPayload(Payload):
    talktracks: Optional[List[TalkTrack]]


class ActivateTalkTrackPayload(Payload):
    talktrack: Optional[TalkTrack]


class FinishTalkTrackPayload(Payload):
    pass
