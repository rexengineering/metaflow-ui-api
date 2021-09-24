import logging
from urllib.parse import urljoin
from typing import Dict

import backoff
from aiohttp.client_exceptions import ClientError
from gql import Client
from gql.client import AsyncClientSession
from gql.transport import aiohttp
from gql.transport.exceptions import TransportError, TransportServerError

from .schema import schema
from ...errors import (
    BridgeNotReachableError,
)
from ...settings import (
    LOG_LEVEL,
    REXFLOW_EXECUTION_TIMEOUT,
)

logger = logging.getLogger(__name__)

# aiohttp info logs are too verbose, forcing them to debug level
if LOG_LEVEL != 'DEBUG':
    aiohttp.log.setLevel(logging.WARNING)


class GQLClient:
    def __init__(self, url: str, path: str = '/graphql'):
        self.url = url
        self.path = path

    def _get_transport(self):
        if '?' in self.url:
            # Do not set path when url has a query string
            # This is required for mock bridge
            graphql_url = self.url
        else:
            graphql_url = urljoin(self.url, self.path)
        transport = aiohttp.AIOHTTPTransport(
            url=graphql_url,
        )
        return transport

    def _get_client(self):
        return Client(
            schema=schema,
            transport=self._get_transport(),
            execute_timeout=REXFLOW_EXECUTION_TIMEOUT,
        )

    @backoff.on_exception(
        backoff.expo,
        TransportServerError,
        max_tries=3,
        logger=logger,
    )
    async def _execute(
        self,
        session: AsyncClientSession,
        query: str,
        params: Dict,
    ) -> Dict:
        try:
            return await session.execute(query, variable_values=params)
        except Exception:
            logger.exception('We had an exception!')
            raise

    async def execute(self, query: str, params: Dict = None) -> Dict:
        client = self._get_client()
        try:
            async with client as session:
                result = await self._execute(session, query, params)
            logger.debug(result)
        except (ClientError, TransportError) as e:
            raise BridgeNotReachableError from e
        finally:
            await client.transport.close()

        return result
