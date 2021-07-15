from gql import Client, gql
from gql.transport import aiohttp


START_TASK_MUTATION = """
mutation StartTask ($startTask: StartTaskInput!) {
  task {
    start(input: $startTask) {
      status
    }
  }
}
"""

COMPLETE_WORKFLOW_MUTATION = """
mutation CompleteWorkflow ($completeWorkflow: CompleteWorkflowInput!) {
  workflow {
    complete (input: $completeWorkflow) {
      status
    }
  }
}
"""


class Scheduler:
    instances = {}

    def __init__(self, iid, callback, task_list):
        if iid not in self.instances:
            self.instances[iid] = {
                'callback': callback,
                'task_list': task_list,
            }
        self.iid = iid
        self.callback = callback
        self.task_list = task_list

    @classmethod
    def get_scheduler(cls, iid):
        if iid in cls.instances:
            return cls(
                iid,
                **cls.instances[iid],
            )
        else:
            return None

    async def _start_task(self, tid):
        query = gql(START_TASK_MUTATION)
        params = {
            'startTask': {
                'iid': self.iid,
                'tid': tid,
            },
        }

        transport = aiohttp.AIOHTTPTransport(
            url=self.callback,
        )

        async with Client(
            transport=transport,
            fetch_schema_from_transport=True,
        ) as session:
            result = await session.execute(query, variable_values=params)

        return result['task']['start']['status'] == 'SUCCESS'

    async def _cancel_workflow(self):
        query = gql(COMPLETE_WORKFLOW_MUTATION)
        params = {
            'completeWorkflow': {
                'iid': self.iid,
            },
        }

        transport = aiohttp.AIOHTTPTransport(
            url=self.callback,
        )

        async with Client(
            transport=transport,
            fetch_schema_from_transport=True,
        ) as session:
            result = await session.execute(query, variable_values=params)

        return result['workflow']['complete']['status'] == 'SUCCESS'

    async def start(self):
        if self.task_list:
            first_task = self.task_list[0]
            await self._start_task(first_task)

    async def next_task(self, tid):
        found = False
        for task in self.task_list:
            if found:
                await self._start_task(task)
                return True
            elif task == tid:
                found = True

        if found:
            await self._cancel_workflow()

        return False
