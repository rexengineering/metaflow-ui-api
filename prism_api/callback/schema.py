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
)
