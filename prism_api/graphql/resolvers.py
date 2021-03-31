from typing import Optional

from ariadne import QueryType


query = QueryType()


@query.field('hello')
async def resolve_hello(*_, name: Optional[str] = 'World'):
    return 'Hello ' + name
