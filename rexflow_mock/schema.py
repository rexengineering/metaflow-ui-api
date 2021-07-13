from ariadne import QueryType, MutationType

from prism_api.rexflow.schema import schema

from .resolvers import (
    resolve_create_instance,
    resolve_get_instances,
    resolve_version,
)

query = QueryType()

query.set_field('version', resolve_version)
query.set_field('getInstances', resolve_get_instances)

query.bind_to_schema(schema)


mutations = MutationType()

mutations.set_field('createInstance', resolve_create_instance)

mutations.bind_to_schema(schema)
