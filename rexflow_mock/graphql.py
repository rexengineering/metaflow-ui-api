from ariadne.asgi import GraphQL
from ariadne.graphql import graphql
from ariadne.exceptions import HttpError
from starlette.requests import Request
from starlette.responses import JSONResponse, PlainTextResponse
from starlette.background import BackgroundTasks

from .schema import schema


class GraphQLBackgroundTask(GraphQL):
    async def get_context_for_request(self, request: Request) -> dict:
        return {
            "request": request,
            "background": BackgroundTasks(),
        }

    async def graphql_http_server(self, request: Request) -> JSONResponse:
        try:
            data = await self.extract_data_from_request(request)
        except HttpError as error:
            return PlainTextResponse(
                error.message or error.status,
                status_code=400,
            )
        context_value = await self.get_context_for_request(request)
        extensions = await self.get_extensions_for_request(
            request,
            context_value,
        )
        middleware = await self.get_middleware_for_request(
            request,
            context_value,
        )
        success, response = await graphql(
            self.schema,
            data,
            context_value=context_value,
            root_value=self.root_value,
            debug=self.debug,
            logger=self.logger,
            error_formatter=self.error_formatter,
            extensions=extensions,
            middleware=middleware,
        )
        status_code = 200 if success else 400
        # the next 2 lines are the ones we had to change
        background = context_value.get('background')
        return JSONResponse(
            response,
            status_code=status_code,
            background=background,
        )


app = GraphQLBackgroundTask(schema, debug=True)
