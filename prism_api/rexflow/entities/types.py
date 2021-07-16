from enum import Enum
from typing import Dict, List, Optional

from pydantic import BaseModel, Field


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
    CANCELED = 'CANCELED'
    ERROR = 'ERROR'
    RUNNING = 'RUNNING'
    START = 'START'
    STARTING = 'STARTING'
    STOPPED = 'STOPPED'
    STOPPING = 'STOPPING'
    UNKNOWN = 'UNKNOWN'


class TaskStatus(str, Enum):
    UP = 'UP'
    DOWN = 'DOWN'


class OperationStatus(str, Enum):
    SUCCESS = 'SUCCESS'
    FAILURE = 'FAILURE'
    WITH_ERRORS = 'WITH_ERRORS'


class ValidatorEnum(str, Enum):
    REQUIRED = 'REQUIRED'
    REGEX = 'REGEX'
    BOOLEAN = 'BOOLEAN'
    INTERVAL = 'INTERVAL'
    PERCENTAGE = 'PERCENTAGE'
    POSITIVE = 'POSITIVE'


class DataType(str, Enum):
    TEXT = 'TEXT'
    CURRENCY = 'CURRENCY'
    INTEGER = 'INTEGER'
    FLOAT = 'FLOAT'
    BOOLEAN = 'BOOLEAN'
    PERCENTAGE = 'PERCENTAGE'
    TABLE = 'TABLE'
    COPY = 'COPY'


class TextVariant(str, Enum):
    BODY1 = 'BODY1'
    BODY2 = 'BODY2'
    H1 = 'H1'
    H2 = 'H2'
    H3 = 'H3'
    H4 = 'H4'
    H5 = 'H5'
    H6 = 'H6'
    SUBTITLE1 = 'SUBTITLE1'
    SUBTITLE2 = 'SUBTITLE2'


class ErrorDetails(BaseModel):
    message: str

    def __str__(self) -> str:
        return self.message


class MetaData(BaseModel):
    key: str
    value: str


class Validator(BaseModel):
    type: ValidatorEnum
    constraint: Optional[str]


class TaskFieldData(BaseModel):
    dataId: DataId
    type: DataType
    order: int
    label: Optional[str]
    data: Optional[str] = Field(alias='value')
    variant: Optional[TextVariant]
    encrypted: bool = False
    validators: List[Validator] = []

    class Config:
        allow_population_by_field_name = True


class Task(BaseModel):
    iid: WorkflowInstanceId
    tid: TaskId
    data: List[TaskFieldData] = []
    status: TaskStatus = TaskStatus.UP

    def get_data_dict(self):
        return {
            d.dataId: d
            for d in self.data
        }


class Workflow(BaseModel):
    iid: WorkflowInstanceId
    did: Optional[WorkflowDeploymentId]
    status: WorkflowStatus
    tasks: List[Task] = []
    metadata: Dict[str, str] = {}

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
    iid_status: WorkflowStatus
    meta_data: Optional[List[MetaData]]
    graphqlUri: Optional[str]
