from fastapi import FastAPI

from prism_api.graphql.app import app as graphql_app

app = FastAPI()


@app.get('/')
async def root():
    return 'Hello World'

app.mount('/query', graphql_app)
