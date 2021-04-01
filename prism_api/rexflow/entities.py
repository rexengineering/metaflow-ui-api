from enum import Enum
from typing import List

from pydantic import BaseModel


class ValidatorEnum(str, Enum):
    REQUIRED = 'REQUIRED'


class FormField(BaseModel):
    question: str
    answer: str = None
    validators: List[ValidatorEnum] = []


class Form(BaseModel):
    fields: List[FormField] = []
