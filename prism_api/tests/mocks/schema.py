from ariadne import QueryType, MutationType

from prism_api.rexflow.schema import schema


query = QueryType()


@query.field('version')
def resolve_version(*_):
    return '0.0.0'


query.bind_to_schema(schema)


mutation = MutationType()


mutation.bind_to_schema(schema)
