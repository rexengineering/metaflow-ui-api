import timeit
from statistics import fmean
import secrets

from gql import Client, gql
from gql.transport.requests import RequestsHTTPTransport


NUMBER_OF_REQUESTS = 100

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


def main():
    session_id = secrets.token_hex()
    print(f'Starting test {session_id}')
    query = gql(QUERY)

    transport = RequestsHTTPTransport(
        url=TEST_URL,
        headers={'session_id': session_id},
    )

    client = Client(
        transport=transport,
        fetch_schema_from_transport=True,
        execute_timeout=300,
    )

    times = []
    try:
        for _ in range(NUMBER_OF_REQUESTS):
            t1 = timeit.default_timer()
            client.execute(query)
            t2 = timeit.default_timer()
            result = t2 - t1
            times.append(result)
    except Exception as ex:
        print('Error!')
        print(repr(ex))
        client.transport.close()
    avgtime = fmean(times)
    print(f'Finished with {session_id}, avg time {avgtime}')


if __name__ == '__main__':
    main()
