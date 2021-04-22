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

GET_TASK_DATA_QUERY = '''
mutation GetTaskData($formInput: TaskMutationFormInput) {
  tasks {
    form(input: $formInput) {
      iid
      tid
      status
      fields {
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
'''


VALIDATE_TASK_DATA_MUTATION = '''
mutation ValidateTaskData($validateTaskInput: TaskMutationValidateInput) {
  tasks {
    validate(input: $validateTaskInput) {
      iid
      tid
      status
      validatorResults {
        validator {
          type
          constraint
        }
        result
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
      validatorResults {
        validator {
          type
          constraint
        }
        result
      }
    }
  }
}
'''

COMPLETE_TASK_MUTATION = '''
mutation CompleteTask($completeTasksInput: TaskMutationCompleteInput!) {
  tasks {
    complete(input: $completeTaskInput) {
      iid
      tid
      status
    }
  }
}
'''
