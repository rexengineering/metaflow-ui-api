from typing import Dict, Union

from .entities.types import (
    DataId,
    TaskId,
    Validator,
    ValidatorEnum,
    WorkflowInstanceId,
)
from .entities.wrappers import ValidatedPayload


class REXFlowError(Exception):
    """Base exception for REXFlow package"""


class ValidationErrorDetails:
    """Triggers when a validator fails on the bridge"""
    iid: WorkflowInstanceId
    tid: TaskId
    errors: Dict[DataId, Dict[str, Union[str, Validator]]]
    message: str

    def __init__(
        self,
        payload: ValidatedPayload,
    ) -> None:
        self.iid = payload.iid
        self.tid = payload.tid
        self.errors = {}
        for field in payload.results:
            if not field.passed:
                for validator in field.results:
                    if not validator.passed:
                        self.add_error(
                            data_id=field.dataId,
                            message=validator.message,
                            validator=Validator(
                                type=ValidatorEnum.REGEX,
                            )
                        )
        self.message = 'validation errors'

    def add_error(self, data_id: DataId, message: str, validator: Validator):
        self.errors[data_id] = {
            'message': message,
            'validator': validator,
        }
