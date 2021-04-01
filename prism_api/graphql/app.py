from ariadne.asgi import GraphQL

from prism_api import settings
from .schema import schema


app = GraphQL(schema, debug=settings.DEBUG)
