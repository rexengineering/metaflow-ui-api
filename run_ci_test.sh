#!/usr/bin/env bash

docker build . -t prismapi_test:latest \
    --build-arg REX_ANACONDA_MACHINE_USER_USERNAME=$REX_ANACONDA_MACHINE_USER_USERNAME \
    --build-arg REX_ANACONDA_MACHINE_USER_PASSWORD=$REX_ANACONDA_MACHINE_USER_PASSWORD \
    --target test 

docker run --rm prismapi_test:latest bash -c "source activate prism-api && coverage report"
