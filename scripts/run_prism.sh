#!/usr/bin/env bash

source activate prism-api
export PYTHONPATH=${PYTHONPATH}:.

echo 'starting uvicorn now'
uvicorn prism_api.app:app --host 0.0.0.0 ${UVICORN_ARGS}
