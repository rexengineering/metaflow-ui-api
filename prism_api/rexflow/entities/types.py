from enum import Enum
from typing import List, Optional

from pydantic import BaseModel

from prism_api.utils import to_camel


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


class TaskFieldData(BaseModel):
    data_id: DataId
    type: DataType
    order: int
    label: Optional[str]
    data: Optional[str]
    encrypted: bool = False
    validators: List[Validator] = []

    class Config:
        alias_generator = to_camel


class Task(BaseModel):
    iid: WorkflowInstanceId
    tid: TaskId
    data: List[TaskFieldData] = []
    status: TaskStatus = TaskStatus.UP

    def get_data_dict(self):
        return {
            d.data_id: d
            for d in self.data
        }


class Workflow(BaseModel):
    iid: WorkflowInstanceId
    did: Optional[WorkflowDeploymentId]
    status: WorkflowStatus
    tasks: List[Task] = []

    def get_task_dict(self):
        return {
            task.tid: task
            for task in self.tasks
        }


class WorkflowDeployment(BaseModel):
    name: str
    deployments: List[WorkflowDeploymentId]


class WorkflowInstanceInfo(BaseModel):
    iid: WorkflowInstanceId
    graphqlUri: Optional[str]
