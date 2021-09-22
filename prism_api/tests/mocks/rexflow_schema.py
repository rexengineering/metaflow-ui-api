from ariadne import QueryType, MutationType, ObjectType

from rexflow_ui.schema import schema

from . import (
    MOCK_DID,
    MOCK_IID,
    MOCK_TID,
)


query = QueryType()


@query.field('version')
def resolve_version(*_):
    return '0.0.0'


@query.field('getInstances')
def resolve_get_instances(*_):
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


@mutation.field('cancelInstance')
def resolve_cancel_instance(*_, input):
    return {
        'did': MOCK_DID,
        'iid': MOCK_IID,
        'iid_status': 'ERROR',
        'status': 'SUCCESS',
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
