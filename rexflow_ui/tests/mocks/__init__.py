from rexflow_ui.entities.types import (
    DataId,
    WorkflowDeploymentId,
    WorkflowInstanceId,
    TaskId,
)

MOCK_TID_BASE: str = 'Activity_abcde_{n}'
MOCK_DATA_ID_BASE: str = 'field_{n}'

MOCK_BRIDGE_URL = 'http://testbridge/'

MOCK_NAME: str = 'process'
MOCK_DID: WorkflowDeploymentId = 'process-123-abc'
MOCK_IID: WorkflowInstanceId = 'process-123-abc-12345678'
MOCK_TID: TaskId = MOCK_TID_BASE.format(n=0)
MOCK_DATA_ID: DataId = MOCK_DATA_ID_BASE.format(n=0)
