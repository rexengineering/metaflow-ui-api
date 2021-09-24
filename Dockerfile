FROM continuumio/miniconda3 as base
LABEL maintainer="REX Engineering <engineering@rexchange.com>"

# Create the directory containing the code.
RUN mkdir -p /code 

WORKDIR /code

RUN apt-get update && \
    apt-get -y install gcc mono-mcs curl && \
    rm -rf /var/lib/apt/lists/*

FROM base as req

COPY environment.yml /code/

RUN conda install anaconda-client
ARG REX_ANACONDA_MACHINE_USER_USERNAME
ARG REX_ANACONDA_MACHINE_USER_PASSWORD
RUN yes | anaconda login --username $REX_ANACONDA_MACHINE_USER_USERNAME --password $REX_ANACONDA_MACHINE_USER_PASSWORD && \
    conda update setuptools && \
    conda update -n base conda --yes && \
    conda env create && \
    conda clean --all --yes

FROM req as build
# Copy the code files.
COPY rexflow_ui /code/rexflow_ui
COPY prism_api /code/prism_api
COPY setup.py /code/setup.py
COPY scripts /code/scripts

FROM build as lint

SHELL ["/bin/bash", "-c"]
RUN source activate prism-api && flake8

FROM build as test

COPY pytest.ini /code/pytest.ini
SHELL ["/bin/bash", "-c"]
RUN source activate prism-api && pytest -m 'ci' --cov prism_api

FROM req as debugger

SHELL ["/bin/bash", "-c"]
RUN source activate prism-api && pip install debugpy -t /tmp --upgrade

FROM build as debug

COPY --from=debugger /tmp/debugpy /tmp/debugpy
EXPOSE 8000
EXPOSE 5678

CMD ["./scripts/run_prism.debug.sh"]

FROM build as rexflow_mock

COPY rexflow_mock /code/rexflow_mock
EXPOSE 8001

CMD ["./scripts/run_rexflow_mock.sh"]

FROM build as container

# Run the app
EXPOSE 8000

CMD ["./scripts/run_prism.sh"]
