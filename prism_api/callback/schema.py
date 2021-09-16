from os import path

import ariadne

from .resolvers import (
    TaskMutations,
    WorkflowMutations,
    query_health,
)


basepath = path.dirname(__file__)
schemapath = path.abspath(path.join(basepath, 'schema'))


typedefs = ariadne.load_schema_from_path(schemapath)

query = ariadne.QueryType()
query.set_field('health', query_health)

mutation = ariadne.MutationType()
mutation.set_field('task', TaskMutations)
mutation.set_field('workflow', WorkflowMutations)


schema = ariadne.make_executable_schema(
    typedefs,
    query,
    mutation,
)
