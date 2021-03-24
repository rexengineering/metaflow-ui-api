import logging
from typing import Dict

from fastapi import APIRouter, Body

from . import store

logger = logging.getLogger(__name__)

router = APIRouter(tags=['state'])


@router.get('/state/{client_id}')
async def read_state(client_id: str):
    return await store.read_state(client_id)


@router.post('/state/{client_id}')
async def save_state(
    client_id: str,
    state: Dict = Body(
        ...,
        example={
            "state": "test"
        },
    ),
):
    return await store.save_state(client_id, state)
