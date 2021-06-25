from uuid import uuid4

from pydantic.types import UUID4

from .entities import (
    TalkTrack,
    TalkTrackId,
    TalkTrackInfo,
    TalkTrackStatus,
)
from .provider import get_talktrack_file_parsed_contents
from .store import Store
from prism_api.graphql.entities.types import SessionId
from prism_api.rexflow import api as rexflow


def load_talktracks():
    Store.clear_talktrack_info()
    talktrack_contents = get_talktrack_file_parsed_contents()
    for content in talktrack_contents:
        talktrack_info = TalkTrackInfo(**content)
        Store.save_talktrack_info(talktrack_info)


def list_talktracks() -> list[TalkTrackInfo]:
    return Store.list_talktrack_info()


async def start_talktrack(
    session_id: SessionId,
    talktrack_id: TalkTrackId,
) -> TalkTrack:
    talktrack_info = Store.get_talktrack_info(talktrack_id)

    if len(Store.get_talktrack_queue(session_id)) == 0:
        status = TalkTrackStatus.ACTIVE
    else:
        status = TalkTrackStatus.QUEUE

    # TODO change to start workflow by name
    workflow = await rexflow.start_workflow(talktrack_info.workflow_name)

    talktrack = TalkTrack(
        id=uuid4(),
        session_id=session_id,
        details=talktrack_info,
        workflow=workflow,
        status=status,
    )
    Store.save_talktrack(talktrack)
    return talktrack


def get_talktrack_queue(session_id: SessionId) -> list[TalkTrack]:
    return Store.get_talktrack_queue(session_id)


def end_talktrack(session_id: SessionId, talktrack_uuid: UUID4) -> None:
    Store.remove_talktrack(session_id, talktrack_uuid)
