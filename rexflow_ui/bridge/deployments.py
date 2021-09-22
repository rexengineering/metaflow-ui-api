from collections import defaultdict
from typing import List

from httpx import AsyncClient, ConnectError

from ..entities.types import WorkflowDeployment
from ..errors import REXFlowNotReachable
from prism_api import settings


async def get_deployments() -> List[WorkflowDeployment]:
    async with AsyncClient() as client:
        try:
            result = await client.get(
                f'{settings.REXFLOW_FLOWD_HOST}/wf_map',
            )
        except ConnectError as e:
            raise REXFlowNotReachable from e

    result.raise_for_status()
    data = result.json()['wf_map']

    deployments_info = defaultdict(lambda: {
        'deployment_ids': [],
        'bridge_url': '',
    })
    for name, deployments in data.items():
        for deployment in deployments:
            if 'id' in deployment:
                deployments_info[name]['deployment_ids'].append(
                    deployment['id'],
                )
            elif 'bridge_url' in deployment:
                deployments_info[name]['bridge_url'] = deployment['bridge_url']  # noqa E501

    return [
        WorkflowDeployment(
            name=name,
            deployments=deployment['deployment_ids'],
            bridge_url=deployment['bridge_url'],
        )
        for name, deployment in deployments_info.items()
    ]
