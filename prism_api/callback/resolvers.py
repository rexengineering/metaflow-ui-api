from ariadne import QueryType, MutationType


query = QueryType()


@query.field('health')
def query_health(*_):
    return 'OK'


mutation = MutationType()


class Task:
    def __init__(self, *_) -> None:
        pass

    async def start(self, info, input):
        return {
            'status': 'SUCCESS',
        }


mutation.set_field('task', Task)


class Workflow:
    def __init__(self, *_) -> None:
        pass

    async def complete(self, info, input):
        return {
            'status': 'SUCCESS',
        }


mutation.set_field('workflow', Workflow)
