import json
import time


class FakeStore:
    def __init__(self, client_id) -> None:
        self.client_id = client_id
        self.data = None

    async def read(self):
        # Fake some loading process
        time.sleep(1)
        return self.data or json.dumps({
            'status': 'ok',
            'client_id': self.client_id,
        })

    async def save(self, state: str):
        # Fake some saving process
        assert isinstance(state, str)
        self.data = state
        time.sleep(1)
