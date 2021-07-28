#!/usr/bin/env bash
source activate prism-api
export PYTHONPATH=${PYTHONPATH}:.

echo "Start rexflow mock server"
uvicorn rexflow_mock.app:app --host 0.0.0.0 --port 8001 --reload
