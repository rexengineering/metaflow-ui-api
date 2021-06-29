#!/usr/bin/env bash

source activate prism-api
export PYTHONPATH=${PYTHONPATH}:.

echo 'Running setup scripts'
python -m prism_api load-talktracks

echo 'Starting uvicorn with debugger now'
python /tmp/debugpy --listen 0.0.0.0:5678 -m uvicorn prism_api.app:app --host 0.0.0.0 --reload ${UVICORN_ARGS}
