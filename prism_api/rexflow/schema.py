from os import path

from graphql import build_ast_schema, parse


schema_files = [
    'schema.graphql',
]


basepath = path.dirname(__file__)


schemas = []
for schema in schema_files:
    filepath = path.abspath(path.join(basepath, 'schema', schema))
    with open(filepath) as f:
        schemas.append(f.read())


schema = build_ast_schema(parse('\n\n'.join(schemas)))
