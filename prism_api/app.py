import logging
import sys

from fastapi import FastAPI, Response
from fastapi.middleware.cors import CORSMiddleware

from prism_api import services, settings
from prism_api.graphql.app import app as graphql_app
from prism_api.state_manager.router import router as state_router

logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)

app = FastAPI()

origins = settings.CORS_ORIGINS
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_methods=['*'],
    allow_origin_regex=settings.CORS_ORIGIN_REGEX,
)


@app.get('/health')
async def health():
    return Response(content='OK', media_type='text/plain')


@app.get('/health/status')
async def liveness():
    services_status = services.check_status()
    response_status = 200

    response = []
    for name, status in services_status.items():
        if status is False:
            response_status = 503
        response.append(f'{name}: {status}')

    return Response(
        content='\n'.join(response),
        status_code=response_status,
        media_type='text/plain',
    )


app.mount('/query', graphql_app)
app.include_router(state_router)
