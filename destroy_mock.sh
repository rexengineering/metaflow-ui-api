#!/usr/bin/env bash

docker-compose -f docker-compose.yml -f docker-compose.debug.yml -f docker-compose.mock.yml down
