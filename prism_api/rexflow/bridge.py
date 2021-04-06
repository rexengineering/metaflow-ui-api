import os
from typing import List

from pydantic import validate_arguments

from . import entities


class REXFlowBridge:
    endpoint = os.getenv('REX_REXFLOW_HOST')

    @classmethod
    @validate_arguments
    async def start_workflow(
        cls,
        deployment_id: entities.WorkflowDeploymentId,
    ) -> entities.Workflow:
        ...

    @validate_arguments
    def __init__(self, workflow: entities.Workflow) -> None:
        self.workflow = workflow

    @validate_arguments
    async def get_task_data(
        self,
        task_ids: List[entities.TaskId],
    ) -> List[entities.Task]:
        ...

    @validate_arguments
    async def save_task_data(
        self,
        tasks: List[entities.Task],
    ) -> List[entities.Task]:
        ...

    @validate_arguments
    async def complete_task(
        self,
        task_ids: List[entities.TaskId],
    ) -> List[entities.Task]:
        ...
