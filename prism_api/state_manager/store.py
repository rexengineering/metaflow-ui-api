"""Manages saving application state"""
import json

from prism_api.tests.utils import FakeStore

# Currently this are placeholder functions that only simulate the API
Store = FakeStore


def serialize_state(state: dict) -> str:
    return json.dumps(state)


def deserialize_state(state_serialized: str) -> dict:
    return json.loads(state_serialized)


async def save_state(client_id, state: dict):
    store = Store(client_id)
    state_serialized = serialize_state(state)
    await store.save(state_serialized)
    return deserialize_state(await store.read())


async def read_state(client_id) -> str:
    store = Store(client_id)
    return deserialize_state(await store.read())
