import ariadne

from . import resolvers as res


typedefs = ariadne.load_schema_from_path('./schema/')

schema = ariadne.make_executable_schema(
    typedefs,
    res.query,
    res.mutation,
    res.workflow_object,
)
