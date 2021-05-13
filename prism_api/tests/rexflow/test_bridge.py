import unittest

from gql import Client, gql

from ..mocks.schema import schema


class TestGraphQLSchema(unittest.TestCase):
    def test_graphql_schema(self):
        client = Client(schema=schema)
        query = gql("""
        query TestVersion {
            version
        }
        """)
        result = client.execute(query)
        expected = {'version': '0.0.0'}
        self.assertEqual(result, expected)
