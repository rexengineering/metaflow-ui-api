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
from prism_api.rexflow.entities.types import WorkflowStatus


def load_talktracks():
    Store.clear_talktrack_info()
    talktrack_contents = get_talktrack_file_parsed_contents()
    for content in talktrack_contents:
        talktrack_info = TalkTrackInfo(**content)
        Store.save_talktrack_info(talktrack_info)


def list_talktracks() -> list[TalkTrackInfo]:
    return Store.list_talktrack_info()


async def _start_step_workflow(talktrack: TalkTrack):
    step = talktrack.details.get_step(talktrack.current_step)
    if step and step.workflow_name and \
       talktrack.workflow_not_started(step.order):
        workflow = await rexflow.start_workflow_by_name(step.workflow_name)
        talktrack.add_workflow(step.order, workflow)


def _update_workflows(talktrack: TalkTrack):
    workflows = rexflow.get_all_workflows()
    for step, workflow in talktrack.workflows_dict.items():
        workflow = workflows[workflow.iid]
        talktrack.add_workflow(step, workflow)


async def start_talktrack(
    session_id: SessionId,
    talktrack_id: TalkTrackId,
) -> TalkTrack:
    talktrack_info = Store.get_talktrack_info(talktrack_id)

    queue_size = len(Store.get_talktrack_queue(session_id))
    if queue_size == 0:
        status = TalkTrackStatus.ACTIVE
    else:
        status = TalkTrackStatus.QUEUE

    talktrack = TalkTrack(
        id=uuid4(),
        order=queue_size + 1,
        session_id=session_id,
        details=talktrack_info,
        status=status,
    )

    if status == TalkTrackStatus.ACTIVE:
        await _start_step_workflow(talktrack)

    Store.save_talktrack(talktrack)
    return talktrack


def get_talktrack_queue(session_id: SessionId) -> list[TalkTrack]:
    talktracks = Store.get_talktrack_queue(session_id)
    for talktrack in talktracks:
        _update_workflows(talktrack)
    return talktracks


async def activate_talktrack(
    session_id: SessionId,
    talktrack_uuid: UUID4,
) -> TalkTrack:
    active_talktrack = Store.get_talktrack(session_id, talktrack_uuid)

    talktracks = Store.get_talktrack_queue(session_id)
    for talktrack in talktracks:
        if talktrack.id != talktrack_uuid:
            talktrack.status = TalkTrackStatus.QUEUE
            Store.save_talktrack(talktrack)

    active_talktrack.status = TalkTrackStatus.ACTIVE
    await _start_step_workflow(active_talktrack)
    _update_workflows(active_talktrack)
    Store.save_talktrack(active_talktrack)
    return active_talktrack


async def activate_talktrack_step(
    session_id: SessionId,
    talktrack_uuid: UUID4,
    step_number: int,
) -> TalkTrack:
    active_talktrack = Store.get_talktrack(session_id, talktrack_uuid)
    active_talktrack.current_step = step_number
    await _start_step_workflow(active_talktrack)
    _update_workflows(active_talktrack)
    Store.save_talktrack(active_talktrack)
    return active_talktrack


async def finish_talktrack(session_id: SessionId, talktrack_uuid: UUID4):
    talktrack = Store.get_talktrack(session_id, talktrack_uuid)
    if talktrack:
        _update_workflows(talktrack)
        for workflow in talktrack.workflows:
            if workflow.status not in (
                WorkflowStatus.COMPLETED,
                WorkflowStatus.ERROR,
            ):
                await rexflow.cancel_workflow(workflow.iid)
        Store.remove_talktrack(session_id, talktrack_uuid)
