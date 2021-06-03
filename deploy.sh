#!/user/bin/env bash

kubectl delete deployment prism-api

docker build . -t prism-api:latest \
--build-arg REX_ANACONDA_MACHINE_USER_USERNAME=$REX_ANACONDA_MACHINE_USER_USERNAME \
--build-arg REX_ANACONDA_MACHINE_USER_PASSWORD=$REX_ANACONDA_MACHINE_USER_PASSWORD

kubectl apply -n default -f charts/prism-api.yaml
