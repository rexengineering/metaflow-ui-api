import logging
import sys

from fastapi import FastAPI

from prism_api.graphql.app import app as graphql_app
from prism_api.state_manager.router import router as state_router

logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)

app = FastAPI()


@app.get('/')
async def root():
    return 'Hello World'

app.mount('/query', graphql_app)
app.include_router(state_router)
