FROM continuumio/miniconda3 as base
LABEL maintainer="REX Engineering <engineering@rexchange.com>"

# Create the directory containing the code.
RUN mkdir -p /code 

WORKDIR /code

RUN apt-get update && \
    apt-get -y install gcc mono-mcs && \
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

FROM req as code
# Copy the code files.
COPY prism_api /code/prism_api
COPY setup.py /code/setup.py
COPY scripts /code/scripts

FROM code as container

# Run the app
EXPOSE 8000

CMD ["./scripts/run_prism.sh"]
