"""Query definitions for GraphQL"""


START_WORKFLOW_MUTATION = '''
mutation StartWorkflow($startWorkflowInput: StartWorkflowInput!) {
  workflow {
    start(input: $startWorkflowInput) {
      status
      iid
      workflow {
        iid
        did
        status
      }
      errors {
        __typename
        ... on ProblemInterface {
          message
        }
      }
    }
  }
}
'''

GET_TASK_DATA_QUERY = '''
query GetTaskData($taskFilter: TaskFilter!) {
  workflows {
    active {
      tasks(filter: $taskFilter) {
        data {
          id
          type
          order
          label
          data
          encrypted
          validators {
            type
            constraint
          }
        }
      }
    }
  }
}
'''


SAVE_TASK_DATA_MUTATION = '''
mutation SaveTaskData($saveTasksInput: SaveTasksInput!) {
  workflow {
    tasks {
      save(input:$saveTasksInput) {
        status
        tasks {
          id
          status
          data {
            id
            type
            order
            label
            data
            encrypted
            validators {
              type
              constraint
            }
          }
        }
        errors {
          __typename
          ... on ProblemInterface {
            message
          }
        }
      }
    }
  }
}
'''

COMPLETE_TASK_MUTATION = '''
mutation CompleteTask($completeTasksInput: CompleteTasksInput!) {
  workflow {
    tasks {
      complete(input: $completeTasksInput) {
        status
        tasks {
          id
          status
          data {
            id
            type
            order
            label
            data
            encrypted
            validators {
              type
              constraint
            }
          }
        }
        errors {
          __typename
          ... on ProblemInterface {
            message
          }
        }
      }
    }
  }
}
'''
