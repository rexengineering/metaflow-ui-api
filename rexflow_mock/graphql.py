from ariadne.asgi import GraphQL

from prism_api.tests.mocks.rexflow_schema import schema


app = GraphQL(schema, debug=True)
