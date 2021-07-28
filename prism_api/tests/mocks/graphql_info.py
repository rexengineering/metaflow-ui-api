"""Mock context data from graphql"""


class MockRequest:
    headers: dict = {}


class MockInfo:
    context: dict = {
        'request': MockRequest(),
        'session_id': 'anon',
    }
