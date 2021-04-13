import logging
import sys

from fastapi import FastAPI, Response

from prism_api.graphql.app import app as graphql_app
from prism_api.state_manager.router import router as state_router

logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)

app = FastAPI()


@app.get('/health')
async def health():
    return Response(content='OK', media_type='text/plain')

app.mount('/query', graphql_app)
app.include_router(state_router)
