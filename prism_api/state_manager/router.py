import json
import logging
from typing import Dict

from fastapi import APIRouter, Body

logger = logging.getLogger(__name__)

router = APIRouter(tags=['state'])


@router.get('/state')
async def read_state():
    return json.loads('{ "state": "ok" }')


@router.post('/state')
async def save_state(
    state: Dict = Body(
        ...,
        example={
            "state": "test"
        },
    )
):
    return {'saved': state}
