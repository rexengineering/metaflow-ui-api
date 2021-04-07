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
