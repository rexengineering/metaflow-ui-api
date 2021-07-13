
workflow_deployments = {
    'CallWorkflow': 'callworkflow-abc123',
    'test': 'another',
}

workflow_instances = {
    did: []
    for did in workflow_deployments.values()
}


async def available_workflows():
    return {
        'message': 'Ok',
        'status': 0,
        'wf_map': {
            name: [
                {
                    'id': did,
                    'start_events_urls': '',
                    'use_opaque_metadata': {},
                }
            ]
            for name, did in workflow_deployments.items()
        }
    }


async def get_workflow_instances(did: str):
    return {
        'did': did,
        'did_status': 'RUNNING',
        'iid_list': workflow_instances.get(did, []),
        'tasks': [],
    }
