from os import path

import ariadne

from . import resolvers

basepath = path.dirname(__file__)
schemapath = path.abspath(path.join(basepath, 'schema'))


typedefs = ariadne.load_schema_from_path(schemapath)


schema = ariadne.make_executable_schema(
    typedefs,
    resolvers.query,
    resolvers.mutation,
    resolvers.workflow_object,
    resolvers.problem_interface,
    resolvers.task_problems_union,
    ariadne.snake_case_fallback_resolvers,
)
