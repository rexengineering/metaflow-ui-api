from starlette.requests import Request
from starlette.background import BackgroundTasks

from .store import Store
from .task_scheduler import Scheduler
from .utils import generate_xid
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

    xid = generate_xid()

    scheduler = Scheduler(iid, callback, await get_task_list(did))
    tid = scheduler.task_list[0]
    Store.save_task(xid, iid, tid)
    background: BackgroundTasks = info.context['background']
    background.add_task(scheduler.start, xid=xid)

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


class TaskExchangeResolver:
    def __init__(self, did):
        self.did = did

    async def form(self, _, input):
        xid = input['xid']
        task = Store.get_task(xid)
        iid = task['iid']
        tid = task['tid']

        return {
            'iid': iid,
            'tid': tid,
            'xid': xid,
            'status': 'SUCCESS',
            'fields': await get_task_fields(self.did, tid),
        }

    async def validate(self, _, input):
        xid = input['xid']
        task = Store.get_task(xid)
        iid = task['iid']
        tid = task['tid']

        return {
            'iid': iid,
            'tid': tid,
            'xid': xid,
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
        xid = input['xid']
        task = Store.get_task(xid)
        iid = task['iid']
        tid = task['tid']

        return {
            'iid': iid,
            'tid': tid,
            'xid': xid,
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
        xid = input['xid']
        task = Store.get_task(xid)
        iid = task['iid']
        tid = task['tid']

        background: BackgroundTasks = info.context['background']
        background.add_task(self._go_to_next_task, iid=iid, tid=tid)

        return {
            'iid': iid,
            'tid': tid,
            'xid': xid,
            'status': 'SUCCESS',
        }


class TaskResolver:
    def __init__(self, _, info):
        self.did = _get_did(info)

    def exchange(self, _):
        return TaskExchangeResolver(self.did)

    async def form(self, _, input):
        iid = input['iid']
        tid = input['tid']

        return {
            'iid': iid,
            'tid': tid,
            'xid': generate_xid(),  # This may cause errors
                                    # but is required by the schema
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

    async def _go_to_next_task(self, iid, tid, xid):
        scheduler: Scheduler = Scheduler.get_scheduler(iid)
        if scheduler:
            result = await scheduler.next_task(tid)
            if result is False:
                await cancel_workflow(self.did, iid)

    async def complete(self, info, input):
        iid = input['iid']
        tid = input['tid']

        xid = generate_xid()
        Store.save_task(xid, iid, tid)
        background: BackgroundTasks = info.context['background']
        background.add_task(self._go_to_next_task, iid=iid, tid=tid, xid=xid)

        return {
            'iid': iid,
            'tid': tid,
            'status': 'SUCCESS',
        }
