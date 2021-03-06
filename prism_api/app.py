import logging
import sys

from fastapi import FastAPI, Response
from fastapi.middleware.cors import CORSMiddleware

from prism_api import services, settings
from prism_api.callback.app import app as callback_app
from prism_api.graphql.app import app as graphql_app
from prism_api.state_manager.router import router as state_router

logging.basicConfig(stream=sys.stdout, level=settings.LOG_LEVEL)

app = FastAPI()

origins = settings.CORS_ORIGINS
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_methods=['*'],
    allow_origin_regex=settings.CORS_ORIGIN_REGEX,
    allow_headers=['authorization', 'x-id-token'],
)


@app.get('/health')
async def health():  # pragma: no cover
    return Response(content='OK', media_type='text/plain')


@app.get('/health/status')
async def liveness():  # pragma: no cover
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


app.mount('/callback', callback_app)
app.mount('/query', graphql_app)
app.include_router(state_router)
