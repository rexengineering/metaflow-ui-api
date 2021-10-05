"""Query definitions for GraphQL"""
# ignore long line on this file
# flake8: noqa: E501


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

CANCEL_WORKFLOW_QUERY = '''
mutation CancelWorkflow($cancelWorkflow: CancelWorkflowInstanceInput!) {
  cancelInstance(input: $cancelWorkflow) {
    did
    iid
    iid_status
    status
  }
}
'''

GET_INSTANCES_QUERY = '''
query GetInstances{
  getInstances {
    did
    iid_list {
      iid
      iid_status
      meta_data {
        key
        value
      }
      tid_list {
        tid
        xid_list {
          xid
          xid_state
        }
      }
    }
  }
}
'''

GET_WORKFLOW_QUERY = '''
query GetWorkflow ($workflowInput: GetInstanceInput!) {
  getInstances (input: $workflowInput) {
    did
    iid_list {
      iid
      iid_status
      meta_data {
        key
        value
      }
      tid_list {
        tid
        xid_list {
          xid
          xid_state
        }
      }
    }
  }
}
'''

GET_TASK_LIST_QUERY = '''
query GetTaskList {
  getInstances {
    tasks
  }
}
'''

GET_TASK_DATA_QUERY = '''
mutation GetTaskData($formInput: TaskMutationFormInput!) {
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
        variant
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
          passed
          message
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
          passed
          message
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

GET_TASK_EXCHANGE_DATA_QUERY = '''
mutation GetTaskData($formInput: TaskExchangeMutationFormInput!) {
  tasks {
    exchange {
      form(input: $formInput) {
        iid
        tid
        xid
        status
        fields {
          dataId
          type
          order
          label
          data
          variant
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


VALIDATE_TASK_EXCHANGE_DATA_MUTATION = '''
mutation ValidateTaskData($validateTaskInput: TaskExchangeMutationValidateInput!) {
  tasks {
    exchange {
      validate(input: $validateTaskInput) {
        iid
        tid
        xid
        status
        passed
        results {
          dataId
          passed
          results {
            passed
            message
          }
        }
      }
    }
  }
}
'''


SAVE_TASK_EXCHANGE_DATA_MUTATION = '''
mutation SaveTaskData($saveTaskInput: TaskExchangeMutationSaveInput!) {
  tasks {
    exchange {
      save(input: $saveTaskInput) {
        iid
        tid
        xid
        status
        passed
        results {
          dataId
          passed
          results {
            passed
            message
          }
        }
      }
    }
  }
}
'''

COMPLETE_TASK_EXCHANGE_MUTATION = '''
mutation CompleteTask($completeTaskInput: TaskExchangeMutationCompleteInput!) {
  tasks {
    exchange {
      complete(input: $completeTaskInput) {
        iid
        tid
        xid
        status
      }
    }
  }
}
'''
