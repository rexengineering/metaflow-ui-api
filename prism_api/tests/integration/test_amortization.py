import asyncio
import unittest

import pytest
from gql import Client, gql
from gql.transport import aiohttp


from ..utils import run_async
from prism_api import settings
from rexflow_ui.entities.types import OperationStatus

AMORT_WORKFLOW_ID = 'AmortTable'

RETRY_LIMIT = 5

AVAILABLE_WORKFLOW_QUERY = '''
query AvailableWorkflow {
    workflows {
        available {
            name
        }
    }
}
'''

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
    settings.RUN_INTEGRATION_TESTS is False,
    reason='Test only run on integration environment',
)
@pytest.mark.integration
class IntegrationTestAmortization(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(
            settings.INTEGRATION_TEST_HOST,
            'Host for integration tests is not set',
        )
        self.client = Client(
            transport=aiohttp.AIOHTTPTransport(
                url=settings.INTEGRATION_TEST_HOST,
            ),
            fetch_schema_from_transport=True,
            execute_timeout=300,
        )

    @run_async
    async def test_amortization_workflow(self):
        # List available workflows
        available_workflow_query = gql(AVAILABLE_WORKFLOW_QUERY)
        async with self.client as session:
            await session.execute(available_workflow_query)

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

        tasks = []
        count = 0
        while len(tasks) == 0:
            count = count + 1
            if count > RETRY_LIMIT:
                print('Exceeded number of retries')
                break

            await asyncio.sleep(1)

            get_task_data_query = gql(GET_TASK_DATA_QUERY)
            get_task_data_params = {
                'workflowFilter': {'ids': [workflow_iid]}
            }

            async with self.client as session:
                result = await session.execute(
                    get_task_data_query,
                    variable_values=get_task_data_params,
                )

            try:
                tasks = result['workflows']['active'][0]['tasks']
            except IndexError:
                tasks = []

        self.assertGreater(count, 0)
        self.assertGreater(len(tasks), 0, f'workflow id {workflow_iid}')
        task_id = tasks[0]['tid']
        self.assertEqual('get_terms', task_id, f'workflow id {workflow_iid}')

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
        self.assertEqual(
            status,
            OperationStatus.SUCCESS,
            f'workflow id {workflow_iid}',
        )
        task = result['workflow']['tasks']['validate']['tasks'][0]
        for data in task['data']:
            self.assertEqual(
                data['data'],
                data_values[data['dataId']],
                'workflow id {workflow_iid}',
            )

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
        self.assertEqual(
            status,
            OperationStatus.SUCCESS,
            f'workflow id {workflow_iid}',
        )
        task = result['workflow']['tasks']['save']['tasks'][0]
        for data in task['data']:
            self.assertEqual(
                data['data'],
                data_values[data['dataId']],
                f'workflow id {workflow_iid}',
            )

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
        self.assertEqual(
            status,
            OperationStatus.SUCCESS,
            f'workflow id {workflow_iid}',
        )
        task = result['workflow']['tasks']['complete']['tasks'][0]
        for data in task['data']:
            self.assertEqual(
                data['data'],
                data_values[data['dataId']],
                f'workflow id {workflow_iid}',
            )

        tasks = []
        count = 0
        while len(tasks) == 0:
            count = count + 1
            if count > RETRY_LIMIT:
                print('Exceeded number of retries')
                break

            await asyncio.sleep(1)

            get_task_data_query = gql(GET_TASK_DATA_QUERY)
            get_task_data_params = {
                'workflowFilter': {'ids': [workflow_iid]}
            }

            async with self.client as session:
                result = await session.execute(
                    get_task_data_query,
                    variable_values=get_task_data_params,
                )

            try:
                tasks = result['workflows']['active'][0]['tasks']
            except IndexError:
                tasks = []

        self.assertGreater(count, 0)
        self.assertGreater(len(tasks), 0, f'workflow id {workflow_iid}')
        task_id = tasks[0]['tid']
        self.assertEqual('show_table', task_id, f'workflow id {workflow_iid}')

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
        self.assertEqual(
            status,
            OperationStatus.SUCCESS,
            f'workflow id {workflow_iid}',
        )

        workflows = [...]
        count = 0
        while len(workflows) > 0:
            count = count + 1
            if count > RETRY_LIMIT:
                print('Exceeded number of retries')
                break

            await asyncio.sleep(1)

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

        self.assertGreater(count, 0)
        self.assertEqual(len(workflows), 0, f'workflow id {workflow_iid}')
