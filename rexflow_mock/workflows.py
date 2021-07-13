
async def available_workflows():
    return {
        'message': 'Ok',
        'status': 0,
        'wf_map': {
            'CallWorkflow': [
                {
                    'id': 'callworkflow-abc123',
                    'start_events_urls': '',
                    'use_opaque_metadata': {},
                }
            ]
        }
    }
