from typing import List, Optional

from pydantic import BaseModel

from prism_api.rexflow.entities import types as e


class Problem(BaseModel):
    message: str


# Wrappers

class StartTaskInput(BaseModel):
    iid: e.WorkflowInstanceId
    tid: e.TaskId


class StartTaskPayload(BaseModel):
    status: e.OperationStatus
    errors: Optional[List[Problem]]


class CompleteWorkflowInput(BaseModel):
    iid: e.WorkflowInstanceId


class CompleteWorkflowPayload(BaseModel):
    status: e.OperationStatus
    errors: Optional[List[Problem]]
