import asyncio
import os
import random
import secrets
import timeit
import traceback
from statistics import fmean


from gql import Client, gql
from gql.transport.aiohttp import AIOHTTPTransport


NUMBER_OF_REQUESTS = 100

TEST_URL = os.getenv('APP_INTEGRATION_TEST_HOST')

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


async def main():
    session_id = secrets.token_hex()
    print(f'Starting test {session_id}')
    query = gql(QUERY)

    transport = AIOHTTPTransport(
        url=TEST_URL,
        headers={'session_id': session_id},
    )

    client = Client(
        transport=transport,
        execute_timeout=300,
    )

    times = []
    try:
        async with client as session:
            for _ in range(NUMBER_OF_REQUESTS):
                await asyncio.sleep(random.random())
                t1 = timeit.default_timer()
                await session.execute(query)
                t2 = timeit.default_timer()
                result = t2 - t1
                times.append(result)
    except Exception:
        print('Error!')
        traceback.print_exc()
        await client.transport.close()
    print(times)
    if times:
        avgtime = fmean(times)
        print(f'Finished with {session_id}, avg time {avgtime}')
    else:
        print('Could not get data points')


if __name__ == '__main__':
    asyncio.run(main())
