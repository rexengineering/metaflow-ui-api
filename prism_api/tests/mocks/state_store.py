import asyncio
import json

from prism_api.state_manager.store.adapters import StoreABC


class FakeStore(StoreABC):
    sleep_time = 1.0

    default = {
        'status': 'ok',
    }

    def __init__(self, client_id) -> None:
        self.client_id = client_id
        self.data = None

    async def read(self):
        # Fake some loading process
        await asyncio.sleep(self.sleep_time)
        return self.data or json.dumps(self.default)

    async def save(self, state: str):
        # Fake some saving process
        assert isinstance(state, str)
        self.data = state
        await asyncio.sleep(self.sleep_time)
