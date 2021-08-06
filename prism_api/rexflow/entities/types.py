from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional

from pydantic import BaseModel, Field

from prism_api.settings import BRIDGE_RATE_LIMIT_SECONDS


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
    COPY = 'COPY'
    TEXT = 'TEXT'
    CURRENCY = 'CURRENCY'
    INTEGER = 'INTEGER'
    FLOAT = 'FLOAT'
    BOOLEAN = 'BOOLEAN'
    PERCENTAGE = 'PERCENTAGE'
    TABLE = 'TABLE'
    WORKFLOW = 'WORKFLOW'


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
    data_id: DataId = Field(..., alias='dataId')
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
            d.data_id: d
            for d in self.data
        }


class Workflow(BaseModel):
    iid: WorkflowInstanceId
    did: Optional[WorkflowDeploymentId]
    name: Optional[str]
    status: WorkflowStatus
    tasks: List[Task] = []
    metadata_dict: Dict[str, str] = {}

    last_update: datetime = None

    @property
    def metadata(self):
        return [
            MetaData(
                key=key,
                value=value,
            )
            for key, value in self.metadata_dict.items()
        ]

    def need_refresh(self) -> bool:
        if BRIDGE_RATE_LIMIT_SECONDS < 1:
            return True

        diff = timedelta(seconds=BRIDGE_RATE_LIMIT_SECONDS)
        return self.last_update is None \
            or (datetime.now() - self.last_update) > diff

    def mark_refresh(self):
        self.last_update = datetime.now()

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
