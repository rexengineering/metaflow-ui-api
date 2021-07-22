import asyncio
import timeit
from statistics import fmean

from gql import Client, gql
from gql.transport import aiohttp


NUMBER_OF_CLIENTS = 10

NUMBER_OF_REQUESTS = 10

TEST_URL = 'http://localhost:8000/query/'

QUERY = """
query GetTaskData {
  workflows {
    active {
      iid
      tasks {
        iid
        tid
        status
        data {
          dataId
          type
          order
          label
          data
          variant
          encrypted
          validators {
            type
            constraint
          }
        }
      }
    }
  }
}
"""


async def execute_petitions(session_id):
    print(f'Starting petitions for {session_id}')
    query = gql(QUERY)

    transport = aiohttp.AIOHTTPTransport(
        url=TEST_URL,
        headers={'session_id': session_id},
        timeout=3000,
    )

    client = Client(
        transport=transport,
        fetch_schema_from_transport=True,
        execute_timeout=300,
    )

    times = []
    try:
        async with client as session:
            for i in range(NUMBER_OF_REQUESTS):
                t1 = timeit.default_timer()
                await session.execute(query)
                t2 = timeit.default_timer()
                result = t2 - t1
                times.append(result)
                # print(f'{session_id} - {i} - {result}')
    except Exception as ex:
        print('Error!')
        print(repr(ex))
        await client.transport.close()
    avgtime = fmean(times)
    print(f'Finished with {session_id}, avg time {avgtime}')


async def main():
    print(f'Starting test for {NUMBER_OF_CLIENTS} clients')
    tasks = []
    for i in range(NUMBER_OF_CLIENTS):
        tasks.append(execute_petitions(f'session_{i}'))

    await asyncio.gather(*tasks)
    print('Finished')


if __name__ == '__main__':
    asyncio.run(main())
