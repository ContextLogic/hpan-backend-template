help: ## Show this help
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)

setup: ## Installs python libraries via poetry and sets up pre-commit
	poetry install
	poetry run pre-commit install

python_shell: ## Opens up a python shell into a running python backend worker server container
	docker exec -ti python-backend-worker-server python3

bash: ## Opens up bash into a running python backend worker server container
	docker exec -ti python-backend-worker-server /bin/bash

ps: ## Lists all the containers running from docker compose file
	docker-compose ps

entrypoint_bash: ## Creates a python backend worker container with bash as the entrypoint instead of running a python backend worker server
	docker run -it --entrypoint /bin/bash python-backend-worker-template_server

build_worker_server: ## Only builds the python backend worker server dockerfile instead of all containers
	docker-compose build server

build_all: ## Builds every docker container
	docker-compose build

up_all: ## Starts all containers in docker compose file and runs them in the background
	docker-compose up -d

down_all: ## Stops all containers in docker compose file
	docker-compose down

up: ## Starts the server and also enables pdb debug
	docker-compose up --no-deps --force-recreate -d server && docker attach python-backend-worker-server || docker-compose logs server

test: ## Runs the tests via pytest
	poetry run pytest

black: ## Runs python black via poetry
	poetry run black .

pylint: ## Runs pylint in the app/ directory via poetry
	poetry run pylint app/

