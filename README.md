# Prism API

## Running application

For a quick setup to run the application, copy the values in `.env.example` to `.env` and run the `./run_mock_local.sh` script, this will setup the project using Docker Compose, and will also run a mock rexflow server that simulates communication to a rexflow cluster.

To run the project with rexflow, you must set the required endpoints to `flowd` and `uibridge` in `REX_REXFLOW_HOST` and `REX_REXFLOW_FLOWD_HOST` and then execute the `run_local.sh` script. You may also need to change the `REX_REXUI_SERVER_CALLBACK_HOST` to an appropiate value to allow callback communication from rexflow uibridge.

## Deploying the application

If you already have a local kubernetes cluster running rexflow, it might be better to deploy the project into the cluster for a better integration. In this case, you can execute the `./deploy.sh` script that will add a pod for the project and redis to the local cluster, using the values in `charts/prism-api.yaml` and `charts/redis.yaml`.

## Running tests and linter

You can run linter and tests inside docker using the ci configuration with `./run_ci_test.sh`.

If you want to be able to run linter and tests directly you should setup the conda environment with `conda env update -f environment.yml`, activate with `conda activate prism-api` and then run the linter with `flake8` and tests with `pytest`. If you want to check the project coverage run `pytest --cov`.

## Debugging the application

If you run the project using the `run_local.sh` or `run_mock_local.sh` scripts, a Python debugger will be available at port `5678`. You can also include the `docker-compose.debug.yml` configuration or use the `debug` target on the docker image to activate the debugger.
