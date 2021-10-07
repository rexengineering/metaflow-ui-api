import asyncio
import logging
from typing import List

from gql import gql
from pydantic import validate_arguments

from . import queries
from .client import GQLClient
from ..base import REXFlowBridgeABC
from ...entities.types import (
    ErrorDetails,
    ExchangeId,
    MetaData,
    OperationStatus,
    Task,
    TaskFieldData,
    TaskId,
    TaskStatus,
    Validator,
    Workflow,
    WorkflowInstanceInfo,
    WorkflowStatus,
)
from ...entities.wrappers import (
    CancelInstancePayload,
    CancelWorkflowInstanceInput,
    CreateInstancePayload,
    CreateWorkflowInstanceInput,
    GetInstancePayload,
    MetaDataInput,
    TaskCompletePayload,
    TaskExchangeMutationCompleteInput,
    TaskExchangeMutationFormInput,
    TaskExchangeMutationSaveInput,
    TaskExchangeMutationValidateInput,
    TaskFieldInput,
    TaskFormPayload,
    TaskMutationCompleteInput,
    TaskMutationFormInput,
    TaskMutationSaveInput,
    TaskMutationValidateInput,
    TaskOperationResults,
    TaskSavePayload,
    TaskValidatePayload,
)
from ...errors import ValidationErrorDetails
from ...settings import REXUI_CALLBACK_HOST


logger = logging.getLogger(__name__)


class REXFlowBridgeGQL(REXFlowBridgeABC):
    @classmethod
    @validate_arguments
    async def start_workflow(
        cls,
        bridge_url: str,
        metadata: List[MetaData] = [],
    ) -> Workflow:
        query = gql(queries.START_WORKFLOW_MUTATION)
        params = {
            'createWorkflow': CreateWorkflowInstanceInput(
                graphqlUri=REXUI_CALLBACK_HOST,
                meta_data=[
                    MetaDataInput(
                        key=data.key,
                        value=data.value,
                    )
                    for data in metadata
                ],
            ).dict(),
        }

        client = GQLClient(bridge_url)
        result = await client.execute(query, params)

        payload = CreateInstancePayload(
            **result['createInstance'],
        )
        return Workflow(
            iid=payload.iid,
            did=payload.did,
            status=WorkflowStatus.STARTING,
            bridge_url=bridge_url,
        )

    @classmethod
    @validate_arguments
    async def get_instances(
        cls,
        bridge_url: str,
    ) -> List[WorkflowInstanceInfo]:
        query = gql(queries.GET_INSTANCES_QUERY)

        client = GQLClient(bridge_url)
        result = await client.execute(query)

        payload = GetInstancePayload(**result['getInstances'])
        return payload.iid_list

    @validate_arguments
    def __init__(self, workflow: Workflow) -> None:
        self.workflow = workflow

    @validate_arguments
    async def update_workflow_data(self) -> Workflow:
        query = gql(queries.GET_WORKFLOW_QUERY)

        client = GQLClient(self.workflow.bridge_url)
        result = await client.execute(
            query,
            {
                'workflowInput': {
                    'iid': self.workflow.iid
                }
            },
        )

        payload = GetInstancePayload(**result['getInstances'])
        instance = payload.iid_list.pop()

        workflow = Workflow(
            did=self.workflow.did,
            iid=instance.iid,
            name=self.workflow.name,
            status=instance.iid_status,
            metadata_dict={
                data.key: data.value
                for data in instance.meta_data
            } if instance.meta_data else {},
            bridge_url=self.workflow.bridge_url,
        )
        self.workflow = workflow
        return workflow

    @validate_arguments
    async def get_task_exchange_data(
        self,
        xid: ExchangeId,
        reset_values: bool = False,
    ) -> Task:
        query = gql(queries.GET_TASK_EXCHANGE_DATA_QUERY)

        client = GQLClient(self.workflow.bridge_url)
        params = {
            'formInput': TaskExchangeMutationFormInput(
                xid=xid,
                reset=reset_values,
            ),
        }
        result = await client.execute(query, params)
        payload = TaskFormPayload(**result['tasks']['exchange']['form'])
        task = Task(
            xid=payload.xid,
            iid=payload.iid,
            tid=payload.tid,
            data=payload.fields,
        )
        return task

    @validate_arguments
    async def get_task_data(
        self,
        task_ids: List[TaskId] = [],
        *,
        reset_values: bool = False
    ) -> List[Task]:
        if len(task_ids) == 0:
            return []

        query = gql(queries.GET_TASK_DATA_QUERY)

        client = GQLClient(self.workflow.bridge_url)

        async_tasks = []
        for task_id in task_ids:
            params = {
                'formInput': TaskMutationFormInput(
                    iid=self.workflow.iid,
                    tid=task_id,
                    reset=reset_values,
                ).dict(),
            }
            async_tasks.append(client.execute(
                query,
                params,
            ))

        results = await asyncio.gather(*async_tasks)

        tasks = []
        for result in results:
            task = Task(
                iid=result['tasks']['form']['iid'],
                tid=result['tasks']['form']['tid'],
                status=TaskStatus.UP,
                data=[
                    TaskFieldData(
                        dataId=field['dataId'],
                        type=field['type'],
                        order=field['order'],
                        label=field['label'],
                        data=field['data'],
                        variant=field['variant'],
                        encrypted=field['encrypted'],
                        validators=[
                            Validator(
                                type=validator['type'],
                                constraint=validator['constraint'],
                            )
                            for validator in field['validators']
                        ] if field['validators'] else [],
                    )
                    for field in result['tasks']['form']['fields']
                ]
            )
            tasks.append(task)
        return tasks

    @validate_arguments
    async def validate_task_data(
        self,
        tasks: List[Task],
    ) -> TaskOperationResults:
        query_tid = gql(queries.VALIDATE_TASK_DATA_MUTATION)
        query_xid = gql(queries.VALIDATE_TASK_EXCHANGE_DATA_MUTATION)

        client = GQLClient(self.workflow.bridge_url)
        async_tasks = []
        for task in tasks:
            if task.xid:
                query = query_xid
                params = {
                    'validateTaskInput': TaskExchangeMutationValidateInput(
                        xid=task.xid,
                        fields=[
                            TaskFieldInput(
                                dataId=field.data_id,
                                data=field.data,
                            )
                            for field in task.data
                        ],
                    ).dict(),
                }
            else:
                query = query_tid
                params = {
                    'validateTaskInput': TaskMutationValidateInput(
                        iid=self.workflow.iid,
                        tid=task.tid,
                        fields=[
                            TaskFieldInput(
                                dataId=field.data_id,
                                data=field.data,
                            )
                            for field in task.data
                        ],
                    ).dict(),
                }
            async_tasks.append(client.execute(
                query,
                params,
            ))

        async_results = await asyncio.gather(*async_tasks)

        tasks_dict = {task.tid: task for task in tasks}
        results = TaskOperationResults()
        for result in async_results:
            payload = TaskValidatePayload(
                **result['tasks']['validate'],
            )
            if payload.status != OperationStatus.SUCCESS:
                results.errors.append(ErrorDetails(message=str(payload)))
            elif not payload.passed:
                results.errors.append(
                    ValidationErrorDetails.init_from_payload(payload=payload)
                )
            else:
                results.successful.append(tasks_dict[payload.tid])

        return results

    @validate_arguments
    async def save_task_data(
        self,
        tasks: List[Task],
    ) -> TaskOperationResults:
        query_tid = gql(queries.SAVE_TASK_DATA_MUTATION)
        query_xid = gql(queries.SAVE_TASK_EXCHANGE_DATA_MUTATION)

        client = GQLClient(self.workflow.bridge_url)
        async_tasks = []
        for task in tasks:
            if task.xid:
                query = query_xid
                params = {
                    'saveTaskInput': TaskExchangeMutationSaveInput(
                        xid=task.xid,
                        fields=[
                            TaskFieldInput(
                                dataId=field.data_id,
                                data=field.data,
                            )
                            for field in task.data
                        ],
                    ).dict(),
                }
            else:
                query = query_tid
                params = {
                    'saveTaskInput': TaskMutationSaveInput(
                        iid=self.workflow.iid,
                        tid=task.tid,
                        fields=[
                            TaskFieldInput(
                                dataId=field.data_id,
                                data=field.data,
                            )
                            for field in task.data
                        ],
                    ).dict(),
                }
            async_tasks.append(client.execute(
                query,
                params,
            ))

        async_results = await asyncio.gather(*async_tasks)

        tasks_dict = {task.tid: task for task in tasks}
        results = TaskOperationResults()
        for result in async_results:
            payload = TaskSavePayload(
                **result['tasks']['save'],
            )
            if payload.status != OperationStatus.SUCCESS:
                results.errors.append(ErrorDetails(message=str(payload)))
            elif not payload.passed:
                results.errors.append(
                    ValidationErrorDetails.init_from_payload(payload=payload)
                )
            else:
                results.successful.append(tasks_dict[payload.tid])

        return results

    @validate_arguments
    async def complete_task(
        self,
        tasks: List[Task],
    ) -> TaskOperationResults:
        query_tid = gql(queries.COMPLETE_TASK_MUTATION)
        query_xid = gql(queries.COMPLETE_TASK_EXCHANGE_MUTATION)

        client = GQLClient(self.workflow.bridge_url)
        async_tasks = []
        for task in tasks:
            if task.xid:
                query = query_xid
                params = {
                    'completeTaskInput': TaskExchangeMutationCompleteInput(
                        xid=task.xid,
                    ).dict(),
                }
            else:
                query = query_tid
                params = {
                    'completeTaskInput': TaskMutationCompleteInput(
                        iid=self.workflow.iid,
                        tid=task.tid,
                    ).dict(),
                }
            async_tasks.append(client.execute(
                query,
                params,
            ))

        async_results = await asyncio.gather(*async_tasks)

        tasks_dict = {task.tid: task for task in tasks}
        results = TaskOperationResults()
        for result in async_results:
            payload = TaskCompletePayload(
                **result['tasks']['complete'],
            )
            if payload.status != OperationStatus.SUCCESS:
                results.errors.append(ErrorDetails(message=str(payload)))
            else:
                results.successful.append(tasks_dict[payload.tid])

        return results

    @validate_arguments
    async def cancel_workflow(self) -> bool:
        query = gql(queries.CANCEL_WORKFLOW_QUERY)
        params = {
            'cancelWorkflow': CancelWorkflowInstanceInput(
                iid=self.workflow.iid,
            ).dict(),
        }

        client = GQLClient(self.workflow.bridge_url)
        result = await client.execute(query, params)

        payload = CancelInstancePayload(
            **result['cancelInstance'],
        )

        return payload.status == OperationStatus.SUCCESS
