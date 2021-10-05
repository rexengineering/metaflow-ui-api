from typing import List, Optional

from pydantic import BaseModel

from rexflow_ui.entities.types import (
    ExchangeId,
    OperationStatus,
    TaskId,
    WorkflowInstanceId,
)


class Problem(BaseModel):
    message: str


# Wrappers

class StartTaskInput(BaseModel):
    iid: WorkflowInstanceId
    tid: TaskId
    xid: Optional[ExchangeId]


class StartTaskPayload(BaseModel):
    status: OperationStatus
    errors: Optional[List[Problem]]


class CompleteWorkflowInput(BaseModel):
    iid: WorkflowInstanceId


class CompleteWorkflowPayload(BaseModel):
    status: OperationStatus
    errors: Optional[List[Problem]]
