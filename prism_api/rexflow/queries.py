"""Query definitions for GraphQL"""


START_WORKFLOW_MUTATION = '''
mutation StartWorkflow($createWorkflow: CreateWorkflowInstanceInput!) {
  createInstance(input: $createWorkflow) {
    did
    iid
    status
    tasks
  }
}
'''

GET_INSTANCES_QUERY = '''
query GetInstances{
  getInstances {
    did
    iid_list {
      iid
    }
  }
}
'''

GET_TASK_DATA_QUERY = '''
mutation GetTaskData($formInput: TaskMutationFormInput) {
  tasks {
    form(input: $formInput) {
      iid
      tid
      status
      fields {
        dataId
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
'''


VALIDATE_TASK_DATA_MUTATION = '''
mutation ValidateTaskData($validateTaskInput: TaskMutationValidateInput!) {
  tasks {
    validate(input: $validateTaskInput) {
      iid
      tid
      status
      passed
      results {
        dataId
        passed
        results {
          validator {
            type
            constraint
          }
          passed
          result
        }
      }
    }
  }
}
'''


SAVE_TASK_DATA_MUTATION = '''
mutation SaveTaskData($saveTaskInput: TaskMutationSaveInput!) {
  tasks {
    save(input: $saveTaskInput) {
      iid
      tid
      status
      passed
      results {
        dataId
        passed
        results {
          validator {
            type
            constraint
          }
          passed
          result
        }
      }
    }
  }
}
'''

COMPLETE_TASK_MUTATION = '''
mutation CompleteTask($completeTaskInput: TaskMutationCompleteInput!) {
  tasks {
    complete(input: $completeTaskInput) {
      iid
      tid
      status
    }
  }
}
'''
