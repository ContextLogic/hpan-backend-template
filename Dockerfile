# Mitigating docker rate limit with this
FROM registry-gitlab.i.wish.com/contextlogic/tooling-image/ubuntu:18.04

RUN apt-get update && apt-get upgrade -y && apt install -y python3-pip && apt-get install -y python3 git curl docker
RUN apt-get update && apt-get install -y libcurl4-gnutls-dev libssl-dev libgnutls28-dev

WORKDIR /usr/src/python-backend-worker-template
COPY . .

RUN pip3 install poetry 
RUN PYTHONIOENCODING=utf8 poetry install --no-dev
ENV PYTHONPATH /usr/src/python-backend-worker-template

EXPOSE 8080
CMD ["python3", "app/server.py"]