import json
import secrets
from os import path


basepath = path.dirname(__file__)
fields_dir = path.abspath(path.join(basepath, 'fields'))


def _transform_field(field):
    field['encrypted'] = field['encrypted'] == 'True'
    return field


def _load_fields(file: str):
    filename = path.join(fields_dir, file)

    with open(filename) as f:
        fields = json.load(f)

    return [
        _transform_field(field)
        for field in fields
    ]


workflow_deployments = {
    'callworkflow-abc123': {
        'name': 'CallWorkflow',
        'did': 'callworkflow-abc123',
        'tasks': {
            'get_call_data': _load_fields('call_fields.json'),
        },
    },
    'buying-abc': {
        'name': 'Buying',
        'did': 'buying-abc',
        'tasks': {
            'buyer': _load_fields('buyer.json'),
            'buyer_form': _load_fields('buyer_form.json'),
        }
    },
}

workflow_instances = {
    info['did']: {}
    for info in workflow_deployments.values()
}


async def available_workflows():
    return {
        'message': 'Ok',
        'status': 0,
        'wf_map': {
            info['name']: [
                {
                    'id': info['did'],
                    'start_events_urls': '',
                    'use_opaque_metadata': {},
                }
            ]
            for info in workflow_deployments.values()
        }
    }


async def get_workflow_instances(did: str):
    return {
        'did': did,
        'did_status': 'RUNNING',
        'iid_list': list(workflow_instances.get(did, {}).values()),
        'tasks': [],
    }


async def start_workflow(did: str, callback: str, metadata: list):
    if did in workflow_instances:
        iid = f'{did}-{secrets.token_hex(8)}'
        workflow_instances[did][iid] = {
            'iid': iid,
            'iid_status': 'RUNNING',
            'graphqlUri': callback,
            'meta_data': metadata,
        }
        return iid
    else:
        return ''


async def cancel_workflow(did: str, iid: str):
    try:
        del workflow_instances[did][iid]
    except KeyError:
        pass


async def get_task_list(did: str):
    try:
        tasks = list(workflow_deployments[did]['tasks'].keys())
    except KeyError:
        tasks = []

    return tasks


async def get_task_fields(did: str, tid: str):
    try:
        return workflow_deployments[did]['tasks'][tid]
    except KeyError:
        return []
