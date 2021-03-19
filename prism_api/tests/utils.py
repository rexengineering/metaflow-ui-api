import json
import time


class FakeStore:
    default = {
        'status': 'ok',
    }

    def __init__(self, client_id) -> None:
        self.client_id = client_id
        self.data = None

    async def read(self):
        # Fake some loading process
        time.sleep(1)
        return self.data or json.dumps(self.default)

    async def save(self, state: str):
        # Fake some saving process
        assert isinstance(state, str)
        self.data = state
        time.sleep(1)
