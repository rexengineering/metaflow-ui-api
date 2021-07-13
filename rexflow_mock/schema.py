from ariadne import QueryType

from prism_api.rexflow.schema import schema

from .resolvers import (
    resolve_version,
    resolve_get_instances,
)

query = QueryType()

query.set_field('version', resolve_version)
query.set_field('getInstances', resolve_get_instances)

query.bind_to_schema(schema)
