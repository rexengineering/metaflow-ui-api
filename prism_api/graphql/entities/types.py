from pydantic import BaseModel


class SessionId(str):
    """Session identifier"""


class State(str):
    """Type representing the client state"""


class Session(BaseModel):
    id: SessionId
    state: State
