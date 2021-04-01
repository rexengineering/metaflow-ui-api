import ariadne

from .resolvers import query


typedefs = ariadne.gql("""
    type Query {
        hello(name: String): String
    }
""")


schema = ariadne.make_executable_schema(typedefs, [query])
