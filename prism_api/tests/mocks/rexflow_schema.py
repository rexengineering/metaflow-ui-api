from ariadne import QueryType, MutationType, ObjectType

from prism_api.rexflow.schema import schema


MOCK_DID = 'process-123-abc'
MOCK_IID = 'process-123-abc-12345678'
MOCK_TID = 'Activity_abcde'


query = QueryType()


@query.field('version')
def resolve_version(*_):
    return '0.0.0'


@query.field('getInstances')
def resolve_get_instances(*_, input):
    return {
        'did': MOCK_DID,
        'did_status': 'RUNNING',
        'iid_list': [
            {
                'iid': MOCK_IID,
                'iid_status': 'RUNNING',
                'graphqlUri': 'http://test/callback',
            },
        ],
        'tasks': [
            MOCK_TID,
        ],
    }


query.bind_to_schema(schema)


mutation = MutationType()
mutation.set_field('tasks', lambda *_: {})
task_mutation = ObjectType('TaskMutation')


@mutation.field('createInstance')
def resolve_create_instance(*_, input):
    return {
        'did': MOCK_DID,
        'iid': MOCK_IID,
        'status': 'SUCCESS',
        'tasks': [],
    }


@task_mutation.field('form')
def resolve_form(*_, input):
    return {
        'iid': input['iid'],
        'tid': input['tid'],
        'status': 'SUCCESS',
        'fields': [
            {
                'dataId': 'uname',
                'type': 'TEXT',
                'order': 1,
                'label': 'username',
                'data': '',
                'encrypted': False,
                'validators': [],
            },
        ]
    }


@task_mutation.field('validate')
def resolve_validate(*_, input):
    return {
        'iid': input['iid'],
        'tid': input['tid'],
        'status': 'SUCCESS',
        'passed': True,
        'results': [],
    }


@task_mutation.field('save')
def resolve_save(*_, input):
    return {
        'iid': input['iid'],
        'tid': input['tid'],
        'status': 'SUCCESS',
        'passed': True,
        'results': [],
    }


@task_mutation.field('complete')
def resolve_complete(*_, input):
    return {
        'iid': input['iid'],
        'tid': input['tid'],
        'status': 'SUCCESS',
    }


mutation.bind_to_schema(schema)
task_mutation.bind_to_schema(schema)
