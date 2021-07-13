import logging
import sys

from fastapi import FastAPI

from .graphql import app as graphql_app

logging.basicConfig(stream=sys.stdout, level=logging.INFO)


app = FastAPI()

app.mount('/graphql', graphql_app)
