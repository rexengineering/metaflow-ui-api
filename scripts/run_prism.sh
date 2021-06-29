#!/usr/bin/env bash

source activate prism-api
export PYTHONPATH=${PYTHONPATH}:.

echo 'Running setup scripts'
python -m prism_api load-talktracks

echo 'Starting uvicorn now'
uvicorn prism_api.app:app --host 0.0.0.0 ${UVICORN_ARGS}
