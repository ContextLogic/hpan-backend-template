# Mitigating docker rate limit with this
FROM registry-gitlab.i.wish.com/contextlogic/tooling-image/ubuntu:18.04

RUN useradd -ms /bin/bash worker

RUN apt-get update && apt-get upgrade -y && apt install -y python3-pip && apt-get install -y python3 git curl docker
RUN apt-get update && apt-get install -y libcurl4-gnutls-dev libssl-dev libgnutls28-dev

WORKDIR /usr/src/python-backend-worker-template
# Only copy dependency files here to get docker to use cached layers if dependencies do not change
COPY pyproject.toml poetry.lock ./
ENV PYTHONPATH /usr/src/python-backend-worker-template

RUN pip3 install poetry 
RUN poetry config experimental.new-installer false && poetry config virtualenvs.create false
RUN PYTHONIOENCODING=utf8 poetry install --no-dev
COPY . .

# setup tmp folder for prometheus_multiproc_dir
ENV prometheus_multiproc_dir=./prometheus_multiproc_dir

RUN chown worker ./
USER worker

EXPOSE 8080
CMD ["python3", "app/worker.py"]