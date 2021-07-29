import asyncio
import os
import unittest

import pytest
from gql import Client, gql
from gql.transport import aiohttp


from ..utils import run_async
from prism_api.rexflow.entities.types import OperationStatus


RUN_INTEGRATION_TESTS = os.getenv('INTEGRATION_TESTS', False)

API_TEST_HOST = 'http://localhost:8000/query/'

AMORT_WORKFLOW_ID = 'AmortTable'

START_WORKFLOW_MUTATION = '''
mutation StartWorkflow ($startWorkflowByNameInput: StartWorkflowByNameInput!) {
    workflow {
        startByName (input: $startWorkflowByNameInput) {
            status
            iid
        }
    }
}
'''

GET_TASK_DATA_QUERY = '''
query GetTaskData ($workflowFilter: WorkflowFilter!) {
  workflows {
    active (filter: $workflowFilter) {
      iid
      tasks {
        tid
        data {
          dataId
          type
          data
        }
      }
    }
  }
}
'''

VALIDATE_TASK_DATA_MUTATION = '''
mutation ValidateTaskData($validateTaskDataInput: ValidateTaskInput!) {
  workflow {
    tasks {
      validate(
        input: $validateTaskDataInput
      ) {
        status
        tasks {
          tid
          data {
            dataId
            data
          }
        }
      }
    }
  }
}
'''

SAVE_TASK_DATA_MUTATION = '''
mutation SaveTaskData($saveTaskDataInput: SaveTasksInput!) {
  workflow {
    tasks {
      save(
        input: $saveTaskDataInput
      ) {
        status
        tasks {
          tid
          data {
            dataId
            data
          }
        }
      }
    }
  }
}
'''

COMPLETE_TASK_DATA_MUTATION = '''
mutation CompleteTaskData($completeTasksInput: CompleteTasksInput!) {
  workflow {
    tasks {
      complete(
        input: $completeTasksInput
      ) {
        status
        tasks {
          tid
          data {
            dataId
            data
          }
        }
      }
    }
  }
}
'''


@pytest.mark.skipif(
    RUN_INTEGRATION_TESTS is False,
    reason='Test only run on integration environment',
)
@pytest.mark.integration
class IntegrationTestAmortization(unittest.TestCase):
    def setUp(self):
        self.client = Client(
            transport=aiohttp.AIOHTTPTransport(url=API_TEST_HOST),
            fetch_schema_from_transport=True,
        )

    @run_async
    async def test_amortization_workflow(self):
        # Workfs for demo_amortization.bpmn
        start_workflow_query = gql(START_WORKFLOW_MUTATION)
        start_workflow_params = {
            'startWorkflowByNameInput': {
                'name': AMORT_WORKFLOW_ID,
            }
        }

        async with self.client as session:
            result = await session.execute(
                start_workflow_query,
                variable_values=start_workflow_params,
            )

        status = result['workflow']['startByName']['status']
        self.assertEqual(status, OperationStatus.SUCCESS)

        workflow_iid = result['workflow']['startByName']['iid']

        await asyncio.sleep(5)

        get_task_data_query = gql(GET_TASK_DATA_QUERY)
        get_task_data_params = {
            'workflowFilter': {'ids': [workflow_iid]}
        }

        async with self.client as session:
            result = await session.execute(
                get_task_data_query,
                variable_values=get_task_data_params,
            )

        tasks = result['workflows']['active'][0]['tasks']
        self.assertGreater(len(tasks), 0)
        task_id = tasks[0]['tid']
        self.assertEqual('get_terms', task_id)

        data_values = {
            'principal': '10000',
            'interest': '3.0',
            'term': '60',
            'seller': 'Underpants',
        }

        task_data = {
            'iid': workflow_iid,
            'tid': task_id,
            'data': [
                {
                    'dataId': dataId,
                    'data': value,
                }
                for dataId, value in data_values.items()
            ]
        }

        validate_task_data_mutation = gql(VALIDATE_TASK_DATA_MUTATION)
        validate_task_data_params = {
            'validateTaskDataInput': {
                'tasks': [task_data]
            },
        }
        async with self.client as session:
            result = await session.execute(
                validate_task_data_mutation,
                variable_values=validate_task_data_params,
            )

        status = result['workflow']['tasks']['validate']['status']
        self.assertEqual(status, OperationStatus.SUCCESS)
        task = result['workflow']['tasks']['validate']['tasks'][0]
        for data in task['data']:
            self.assertEqual(data['data'], data_values[data['dataId']])

        save_task_data_mutation = gql(SAVE_TASK_DATA_MUTATION)
        save_task_data_params = {
            'saveTaskDataInput': {
                'tasks': [task_data]
            },
        }
        async with self.client as session:
            result = await session.execute(
                save_task_data_mutation,
                variable_values=save_task_data_params,
            )

        status = result['workflow']['tasks']['save']['status']
        self.assertEqual(status, OperationStatus.SUCCESS)
        task = result['workflow']['tasks']['save']['tasks'][0]
        for data in task['data']:
            self.assertEqual(data['data'], data_values[data['dataId']])

        complete_task_data_mutation = gql(COMPLETE_TASK_DATA_MUTATION)
        complete_task_data_params = {
            'completeTasksInput': {
                'tasks': [task_data]
            },
        }
        async with self.client as session:
            result = await session.execute(
                complete_task_data_mutation,
                variable_values=complete_task_data_params,
            )

        status = result['workflow']['tasks']['complete']['status']
        self.assertEqual(status, OperationStatus.SUCCESS)
        task = result['workflow']['tasks']['complete']['tasks'][0]
        for data in task['data']:
            self.assertEqual(data['data'], data_values[data['dataId']])

        await asyncio.sleep(5)

        get_task_data_query = gql(GET_TASK_DATA_QUERY)
        get_task_data_params = {
            'workflowFilter': {'ids': [workflow_iid]}
        }

        async with self.client as session:
            result = await session.execute(
                get_task_data_query,
                variable_values=get_task_data_params,
            )

        tasks = result['workflows']['active'][0]['tasks']
        self.assertGreater(len(tasks), 0)
        task_id = tasks[0]['tid']
        self.assertEqual('show_table', task_id)

        complete_task_data_mutation = gql(COMPLETE_TASK_DATA_MUTATION)
        complete_task_data_params = {
            'completeTasksInput': {
                'tasks': [{
                    'iid': workflow_iid,
                    'tid': task_id,
                    'data': [],
                }]
            },
        }
        async with self.client as session:
            result = await session.execute(
                complete_task_data_mutation,
                variable_values=complete_task_data_params,
            )

        status = result['workflow']['tasks']['complete']['status']
        self.assertEqual(status, OperationStatus.SUCCESS)

        await asyncio.sleep(5)

        get_task_data_query = gql(GET_TASK_DATA_QUERY)
        get_task_data_params = {
            'workflowFilter': {'ids': [workflow_iid]}
        }

        async with self.client as session:
            result = await session.execute(
                get_task_data_query,
                variable_values=get_task_data_params,
            )

        workflows = result['workflows']['active']
        self.assertEqual(len(workflows), 0)
