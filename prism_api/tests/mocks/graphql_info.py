"""Mock context data from graphql"""
from dataclasses import dataclass, field


@dataclass
class MockRequest:
    headers: dict = field(default_factory=dict)


def _context_factory():
    return {
        'request': MockRequest(),
        'session_id': 'anon',
    }


@dataclass
class MockInfo:
    context: dict = field(default_factory=_context_factory)
