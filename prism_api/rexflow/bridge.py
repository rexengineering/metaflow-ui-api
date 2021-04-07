import logging
from typing import List

from gql import Client, gql
from gql.transport.aiohttp import AIOHTTPTransport
from pydantic import validate_arguments

from prism_api import settings
from . import entities, queries


logger = logging.getLogger(__name__)


class REXFlowBridge:
    transport = AIOHTTPTransport(
        url=settings.REXFLOW_HOST
    )

    @classmethod
    @validate_arguments
    async def start_workflow(
        cls,
        deployment_id: entities.WorkflowDeploymentId,
    ) -> entities.Workflow:
        async with Client(
            transport=cls.transport,
            fetch_schema_from_transport=True,
        ) as session:
            query = gql(queries.START_WORKFLOW_MUTATION)
            params = {
                'startWorkflowInput': entities.StartWorkflowInput(
                    did=deployment_id
                ).dict(),
            }

            result = await session.execute(query, variable_values=params)
            logger.info(result)
            payload = result['workflow']['start']
            return entities.StartWorkflowPayload(**payload)

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
