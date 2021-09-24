

class REXFlowStoreError(Exception):
    """Base exception for REXFlow Store"""


class WorkflowNotFoundError(REXFlowStoreError):
    """Workflow is not found in storage"""


class TaskNotFoundError(REXFlowStoreError):
    """Task is not found in storage"""
