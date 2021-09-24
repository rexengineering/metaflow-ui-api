from __future__ import annotations
from typing import Dict, Union

from .entities.types import (
    DataId,
    ErrorDetails,
    TaskId,
    Validator,
    ValidatorEnum,
    WorkflowInstanceId,
)
from .entities.wrappers import ValidatedPayload


class REXFlowError(Exception):
    """Base exception for REXFlow package"""


class REXFlowNotReachable(REXFlowError):
    """Exception when connecition with flowd fails"""


class BridgeNotReachableError(REXFlowError):
    """Exception when connection with rexflow bridge fails"""


class ValidationErrorDetails(ErrorDetails):
    """Triggers when a validator fails on the bridge"""
    iid: WorkflowInstanceId
    tid: TaskId
    errors: Dict[DataId, Dict[str, Union[str, Validator]]] = {}

    @classmethod
    def init_from_payload(
        cls,
        payload: ValidatedPayload,
    ) -> ValidationErrorDetails:  # Requires future import
        obj = cls(
            iid=payload.iid,
            tid=payload.tid,
            message='validation errors',
        )
        for field in payload.results:
            if not field.passed:
                for validator in field.results:
                    if not validator.passed:
                        obj.add_error(
                            data_id=field.dataId,
                            message=validator.message,
                            validator=Validator(
                                type=ValidatorEnum.REGEX,
                            )
                        )
        return obj

    def add_error(self, data_id: DataId, message: str, validator: Validator):
        self.errors[data_id] = {
            'message': message or 'No details provided',
            'validator': validator,
        }
