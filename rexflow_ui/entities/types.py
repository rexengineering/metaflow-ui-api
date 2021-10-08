from enum import Enum
from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class WorkflowDeploymentId(str):
    """Identifier for a workflow deployment"""


class WorkflowInstanceId(str):
    """Identifier for a workflow instance"""


class TaskId(str):
    """Identifier for Task"""


class ExchangeId(str):
    """Identifier for an specific instance of a task"""


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


class ExchangeState(str, Enum):
    STARTED = 'STARTED'
    SAVED = 'SAVED'
    COMPLETE = 'COMPLETE'


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
    xid: Optional[ExchangeId]
    iid: WorkflowInstanceId
    tid: TaskId
    data: List[TaskFieldData] = []
    status: TaskStatus = TaskStatus.UP
    xid_state: ExchangeState = ExchangeState.STARTED

    def get_data_dict(self):
        return {
            d.data_id: d
            for d in self.data
        }

    def update_task_data(self, data: Dict[DataId, str]):
        data_dict = self.get_data_dict()
        for data_id, value in data.items():
            data_dict[data_id].data = value  # This update the reference


class Workflow(BaseModel):
    iid: WorkflowInstanceId
    did: Optional[WorkflowDeploymentId]
    name: Optional[str]
    status: WorkflowStatus
    tasks: List[Task] = []
    task_xids: List[ExchangeId] = []
    metadata_dict: Dict[str, str] = {}

    bridge_url: Optional[str]

    @property
    def metadata(self):
        return [
            MetaData(
                key=key,
                value=value,
            )
            for key, value in self.metadata_dict.items()
        ]

    def verify_metadata(self, metadata: Dict) -> bool:
        for key, value in metadata.items():
            if self.metadata_dict[key] != value:
                return False

        return True

    def get_task_dict(self):
        return {
            task.tid: task
            for task in self.tasks
        }


class WorkflowDeployment(BaseModel):
    name: str
    deployments: List[WorkflowDeploymentId]
    bridge_url: str

    @property
    def did(self):
        if self.deployments:
            return self.deployments[0]
        return None


class ExchangeInfo(BaseModel):
    xid: ExchangeId
    xid_state: ExchangeState


class TaskExchangeInfo(BaseModel):
    xid: TaskId
    xid_list: List[ExchangeInfo]


class WorkflowInstanceInfo(BaseModel):
    iid: WorkflowInstanceId
    iid_status: WorkflowStatus
    meta_data: Optional[List[MetaData]]
    graphqlUri: Optional[str]
    tid_list: Optional[List[TaskExchangeInfo]]
