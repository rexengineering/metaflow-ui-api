#!/usr/bin/env bash

source activate prism-api
export PYTHONPATH=${PYTHONPATH}:.

echo 'starting gunicorn with uvicorn workers now'
gunicorn prism_api.app:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
