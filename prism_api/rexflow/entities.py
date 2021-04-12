from enum import Enum
from typing import Dict, List, Optional

from pydantic import BaseModel


class WorkflowDeploymentId(str):
    """Identifier for a workflow deployment"""


class WorkflowInstanceId(str):
    """Identifier for a workflow instance"""


class TaskId(str):
    """Identifier for Task"""


class DataId(str):
    """Identifier for data element"""


class WorkflowStatus(str, Enum):
    COMPLETED = 'COMPLETED'
    ERROR = 'ERROR'
    RUNNING = 'RUNNING'
    START = 'START'
    STARTING = 'STARTING'
    STOPPED = 'STOPPED'
    STOPPING = 'STOPPING'


class TaskStatus(str, Enum):
    UP = 'UP'
    DOWN = 'DOWN'


class OperationStatus(str, Enum):
    SUCCESS = 'SUCCESS'
    FAILURE = 'FAILURE'


class ValidatorEnum(str, Enum):
    REQUIRED = 'REQUIRED'
    REGEX = 'REGEX'


class DataType(str, Enum):
    TEXT = 'TEXT'


class Validator(BaseModel):
    type: ValidatorEnum
    constraint: Optional[str]


class TaskData(BaseModel):
    id: DataId
    type: DataType
    order: int
    label: Optional[str]
    data: Optional[str]
    encrypted: bool = False
    validators: List[Validator] = []


class Task(BaseModel):
    iid: WorkflowInstanceId
    id: TaskId
    data: List[TaskData] = []
    status: TaskStatus = TaskStatus.UP

    def get_data_dict(self):
        return {
            d.id: d
            for d in self.data
        }


class Workflow(BaseModel):
    iid: WorkflowInstanceId
    did: Optional[WorkflowDeploymentId]
    status: WorkflowStatus
    tasks: List[Task] = []

    def get_task_dict(self):
        return {
            task.id: task
            for task in self.tasks
        }


# GraphQL filter types

class WorkflowFilter(BaseModel):
    ids: List[WorkflowInstanceId]
    status: Optional[WorkflowStatus]


class TaskFilter(BaseModel):
    ids: List[TaskId] = []
    status: Optional[TaskStatus]


# GraphQL input types

class StartWorkflowInput(BaseModel):
    did: WorkflowDeploymentId  # deployment id


class CompleteWorkflowInput(BaseModel):
    iid: WorkflowInstanceId


class ValidatorInput(BaseModel):
    type: ValidatorEnum
    constraint: Optional[str]


class TaskDataStartInput(BaseModel):
    id: DataId
    type: DataType
    order: int
    label: Optional[str]
    data: Optional[str]
    encrypted: bool = False
    validators: List[ValidatorInput] = []


class TaskStartInput(BaseModel):
    iid: WorkflowInstanceId
    id: TaskId
    data: List[TaskDataStartInput]

    def to_task(self):
        return Task(
            iid=self.iid,
            id=self.id,
            data=[TaskData(**d.dict()) for d in self.data],
        )


class StartTasksInput(BaseModel):
    tasks: List[TaskStartInput]


class TaskDataInput(BaseModel):
    id: DataId
    data: str


class TaskInput(BaseModel):
    iid: WorkflowInstanceId
    id: TaskId
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
    status: OperationStatus
    errors: Optional[List[Problem]]
    query: Dict = {}


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
