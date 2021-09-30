from starlette.requests import Request
from starlette.background import BackgroundTasks

from .task_scheduler import Scheduler
from .workflows import (
    cancel_workflow,
    get_task_fields,
    get_task_list,
    get_workflow_instances,
    start_workflow,
)


async def resolve_version(*_):
    return '0.0.0.mock'


def _get_did(info):
    request: Request = info.context['request']
    return request.query_params.get('did')


async def resolve_get_instances(_, info, input=None):
    input = input or {}
    did = _get_did(info)
    return await get_workflow_instances(did, iid=input.get('iid'))


async def resolve_create_instance(_, info, input):
    did = _get_did(info)
    callback = input['graphqlUri']
    metadata = input.get('meta_data', [])
    iid = await start_workflow(did, callback, metadata)

    scheduler = Scheduler(iid, callback, await get_task_list(did))
    background: BackgroundTasks = info.context['background']
    background.add_task(scheduler.start)

    return {
        'did': did,
        'iid': iid,
        'status': 'SUCCESS' if iid else 'FAILURE',
        'tasks': [],
    }


async def resolve_cancel_instance(_, info, input):
    did = _get_did(info)
    iid = input['iid']
    await cancel_workflow(did, iid)
    return {
        'did': did,
        'iid': iid,
        'iid_status': 'ERROR',
        'status': 'SUCCESS',
    }


class TaskResolver:
    def __init__(self, _, info):
        self.did = _get_did(info)

    async def form(self, _, input):
        iid = input['iid']
        tid = input['tid']

        return {
            'iid': iid,
            'tid': tid,
            'status': 'SUCCESS',
            'fields': await get_task_fields(self.did, tid),
        }

    async def validate(self, _, input):
        iid = input['iid']
        tid = input['tid']

        return {
            'iid': iid,
            'tid': tid,
            'status': 'SUCCESS',
            'passed': True,
            'results': [
                {
                    'dataId': field['dataId'],
                    'passed': True,
                    'results': [],
                }
                for field in input['fields']
            ],
        }

    async def save(self, _, input):
        iid = input['iid']
        tid = input['tid']

        return {
            'iid': iid,
            'tid': tid,
            'status': 'SUCCESS',
            'passed': True,
            'results': [
                {
                    'dataId': field['dataId'],
                    'passed': True,
                    'results': [],
                }
                for field in input['fields']
            ],
        }

    async def _go_to_next_task(self, iid, tid):
        scheduler: Scheduler = Scheduler.get_scheduler(iid)
        if scheduler:
            result = await scheduler.next_task(tid)
            if result is False:
                await cancel_workflow(self.did, iid)

    async def complete(self, info, input):
        iid = input['iid']
        tid = input['tid']

        background: BackgroundTasks = info.context['background']
        background.add_task(self._go_to_next_task, iid=iid, tid=tid)

        return {
            'iid': iid,
            'tid': tid,
            'status': 'SUCCESS',
        }
