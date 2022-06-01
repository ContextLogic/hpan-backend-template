# python-backend-worker-template
This is a template python repo that contains the skeleton to create new backend worker at Wish.
It is a light-weighted wrapper based off celery worker and flask in WSGI server. It utilizes celery + SQS as broker, provides convenience in both producer and consumer ends

It contains the following:

BE worker skeleton code
Tests
Metrics
Dockerfiles
Gitlab CI files for automating the building and registering of new container images
Tracing

# Setting up a new worker
## Pre-step
We recommend to use Python version >= 3.7 to develop the worker. It does not support any Python 2.x, and may be broken in some Python < 3.7 versions (we didn't test)

## 1. Create a Project off the Template（skip this if your repo is created by one-click)
You can setup a new worker repo on the template page [here](https://github.com/ContextLogic/python-backend-worker-template/generate).

Note: The name of the Repository should be the name of the Worker.

Fill in the Repository name, and the Description. Double check the repository is set to Private.

## 2. Migrate Project to Gitlab
Once the project is in Github, send a message to the #Gitlab slack channel with the link of your new repository asking for your repository to be linked to Gitlab.

## 3. Testing Your Worker Locally (PLEASE CONNECT TO VPN)

### pre-step
Setup AWS CREDENTIALS
please make sure that you've setup your AWS credentials at `~/.aws/credentials` and setup the env vars of 
```bash
AWS_SECRET_ACCESS_KEY=xxxx...
AWS_ACCESS_KEY_ID=xxxx...
```

### I. run from source code

### II. run from docker-compose

## 4. Integrations
### sentry integration
### ratelimit integration
### td integration

# Develop your worker
### you can start working on the job processing logic at app/tasks/tasks.py

# Code Layout
# FAQ
