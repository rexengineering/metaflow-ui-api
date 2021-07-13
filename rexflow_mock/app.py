import logging
import sys

from fastapi import FastAPI

from .graphql import app as graphql_app
from .workflows import available_workflows

logging.basicConfig(stream=sys.stdout, level=logging.INFO)


app = FastAPI()

app.add_api_route('/wf_map', available_workflows)

app.mount('/graphql', graphql_app)
