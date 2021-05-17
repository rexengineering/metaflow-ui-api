from ariadne.asgi import GraphQL

from .schema import schema
from prism_api import settings


app = GraphQL(schema, debug=settings.DEBUG)
