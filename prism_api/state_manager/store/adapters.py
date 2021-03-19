import abc


class StoreABC(abc.ABC):
    def __init__(self, client_id: str):
        pass

    def read(self) -> str:
        raise NotImplementedError

    def save(self, state: str) -> str:
        raise NotImplementedError
