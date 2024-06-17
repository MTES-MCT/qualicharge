# -- General
SHELL := /bin/bash

# -- Docker
COMPOSE                = bin/compose
COMPOSE_RUN            = $(COMPOSE) run --rm --no-deps
COMPOSE_RUN_API        = $(COMPOSE_RUN) api
COMPOSE_RUN_API_PIPENV = $(COMPOSE_RUN_API) pipenv run
COMPOSE_RUN_CLIENT     = $(COMPOSE_RUN) client

# -- Tools
CURL = $(COMPOSE_RUN) curl

# -- Ressources
IRVE_STATIC_DATASET_URL = https://www.data.gouv.fr/fr/datasets/r/eb76d20a-8501-400e-b336-d85724de5435
AFIREV_CHARGING_DATASET_URL = https://afirev.fr/en/liste-des-identifiants-attribues/

# ==============================================================================
# RULES

default: help

# -- Files
data:
	mkdir data

data/irve-statique.csv: data
	$(CURL) -L -o /work/data/irve-statique.csv $(IRVE_STATIC_DATASET_URL)

data/afirev-charging.csv: data
	@echo "You should download CSV file from $(AFIREV_CHARGING_DATASET_URL)"

# -- Docker/compose
bootstrap: ## bootstrap the project for development
bootstrap: \
  data/irve-statique.csv \
  build \
  migrate-api \
  create-api-test-db \
	create-metabase-db \
  seed-oidc \
  create-superuser
.PHONY: bootstrap

build: ## build services image
	$(COMPOSE) build
.PHONY: build

build-api: ## build the api image
	$(COMPOSE) build api
.PHONY: build-api

build-client: ## build the client image
	$(COMPOSE) build client
.PHONY: build-client

down: ## stop and remove all containers
	@$(COMPOSE) down
.PHONY: down

logs: ## display all services logs (follow mode)
	@$(COMPOSE) logs -f
.PHONY: logs

logs-api: ## display API server logs (follow mode)
	@$(COMPOSE) logs -f api
.PHONY: logs-api

run: ## run the api server (and dependencies)
	$(COMPOSE) up -d api
.PHONY: run

run-all: ## run the whole stack
	$(COMPOSE) up -d api keycloak metabase
.PHONY: run-all

status: ## an alias for "docker compose ps"
	@$(COMPOSE) ps
.PHONY: status

stop: ## stop all servers
	@$(COMPOSE) stop
.PHONY: stop

# -- Provisioning
create-api-test-db: ## create API test database
	@echo "Creating api service test database…"
	@$(COMPOSE) exec postgresql bash -c 'psql "postgresql://$${POSTGRES_USER}:$${POSTGRES_PASSWORD}@$${QUALICHARGE_DB_HOST}:$${QUALICHARGE_DB_PORT}/postgres" -c "create database \"$${QUALICHARGE_TEST_DB_NAME}\";"' || echo "Duly noted, skipping database creation."
	@$(COMPOSE) exec postgresql bash -c 'psql "postgresql://$${POSTGRES_USER}:$${POSTGRES_PASSWORD}@$${QUALICHARGE_DB_HOST}:$${QUALICHARGE_DB_PORT}/$${QUALICHARGE_TEST_DB_NAME}" -c "create extension postgis;"' || echo "Duly noted, skipping extension creation."
.PHONY: create-api-test-db

create-metabase-db: ## create metabase database
	@echo "Creating metabase service database…"
	@$(COMPOSE) exec postgresql bash -c 'psql "postgresql://$${POSTGRES_USER}:$${POSTGRES_PASSWORD}@$${QUALICHARGE_DB_HOST}:$${QUALICHARGE_DB_PORT}/postgres" -c "create database \"$${MB_DB_DBNAME}\";"' || echo "Duly noted, skipping database creation."
.PHONY: create-metabase-db

drop-api-test-db: ## drop API test database
	@echo "Droping api service test database…"
	@$(COMPOSE) exec postgresql bash -c 'psql "postgresql://$${POSTGRES_USER}:$${POSTGRES_PASSWORD}@$${QUALICHARGE_DB_HOST}:$${QUALICHARGE_DB_PORT}/postgres" -c "drop database \"$${QUALICHARGE_TEST_DB_NAME}\";"' || echo "Duly noted, skipping database deletion."
.PHONY: drop-api-test-db

drop-api-db: ## drop API database
	@echo "Droping api service database…"
	@$(COMPOSE) exec postgresql bash -c 'psql "postgresql://$${POSTGRES_USER}:$${POSTGRES_PASSWORD}@$${QUALICHARGE_DB_HOST}:$${QUALICHARGE_DB_PORT}/postgres" -c "drop database \"$${QUALICHARGE_DB_NAME}\";"' || echo "Duly noted, skipping database deletion."
.PHONY: drop-api-db

drop-metabase-db: ## drop Metabase database
	@echo "Droping metabase service database…"
	@$(COMPOSE) exec postgresql bash -c 'psql "postgresql://$${POSTGRES_USER}:$${POSTGRES_PASSWORD}@$${QUALICHARGE_DB_HOST}:$${QUALICHARGE_DB_PORT}/postgres" -c "drop database \"$${MB_DB_DBNAME}\";"' || echo "Duly noted, skipping database deletion."
.PHONY: drop-metabase-db

migrate-api:  ## run alembic database migrations for the api service
	@echo "Running api service database engine…"
	@$(COMPOSE) up -d --wait postgresql
	@echo "Creating api service database…"
	@$(COMPOSE) exec postgresql bash -c 'psql "postgresql://$${POSTGRES_USER}:$${POSTGRES_PASSWORD}@$${QUALICHARGE_DB_HOST}:$${QUALICHARGE_DB_PORT}/postgres" -c "create database \"$${QUALICHARGE_DB_NAME}\";"' || echo "Duly noted, skipping database creation."
	@$(COMPOSE) exec postgresql bash -c 'psql "postgresql://$${POSTGRES_USER}:$${POSTGRES_PASSWORD}@$${QUALICHARGE_DB_HOST}:$${QUALICHARGE_DB_PORT}/$${QUALICHARGE_DB_NAME}" -c "create extension postgis;"' || echo "Duly noted, skipping extension creation."
	@echo "Running migrations for api service…"
	@bin/alembic upgrade head
.PHONY: migrate-api

create-superuser: ## create super user
	@echo "Creating super user…"
	@$(COMPOSE_RUN_API_PIPENV) python -m qualicharge create-user \
		admin \
		--email admin@example.com \
		--password admin \
		--is-active \
		--is-superuser \
		--is-staff \
		--force
.PHONY: create-superuser

seed-oidc: ## seed the OIDC provider
	@echo 'Starting OIDC provider…'
	@$(COMPOSE) up -d keycloak
	@$(COMPOSE_RUN) dockerize -wait http://keycloak:8080 -timeout 60s
	@echo 'Seeding OIDC client…'
	@$(COMPOSE) exec keycloak /usr/local/bin/kc-init
.PHONY: seed-oidc

# -- API
lint: ## lint all sources
lint: \
	lint-api \
	lint-client
.PHONY: lint

lint-api: ## lint api python sources
lint-api: \
  lint-api-black \
  lint-api-ruff \
  lint-api-mypy
.PHONY: lint-api

lint-client: ## lint api python sources
lint-client: \
  lint-client-black \
  lint-client-ruff \
  lint-client-mypy
.PHONY: lint-client

lint-api-black: ## lint api python sources with black
	@echo 'lint:black started…'
	@$(COMPOSE_RUN_API_PIPENV) black qualicharge tests
.PHONY: lint-api-black

lint-api-ruff: ## lint api python sources with ruff
	@echo 'lint:ruff started…'
	@$(COMPOSE_RUN_API_PIPENV) ruff check qualicharge tests
.PHONY: lint-api-ruff

lint-api-ruff-fix: ## lint and fix api python sources with ruff
	@echo 'lint:ruff-fix started…'
	@$(COMPOSE_RUN_API_PIPENV) ruff check --fix qualicharge tests
.PHONY: lint-api-ruff-fix

lint-api-mypy: ## lint api python sources with mypy
	@echo 'lint:mypy started…'
	@$(COMPOSE_RUN_API_PIPENV) mypy qualicharge tests
.PHONY: lint-api-mypy

lint-client-black: ## lint api python sources with black
	@echo 'lint:black started…'
	@$(COMPOSE_RUN_CLIENT) black qcc tests
.PHONY: lint-client-black

lint-client-ruff: ## lint api python sources with ruff
	@echo 'lint:ruff started…'
	@$(COMPOSE_RUN_CLIENT) ruff check qcc tests
.PHONY: lint-client-ruff

lint-client-ruff-fix: ## lint and fix api python sources with ruff
	@echo 'lint:ruff-fix started…'
	@$(COMPOSE_RUN_CLIENT) ruff check --fix qcc tests
.PHONY: lint-client-ruff-fix

lint-client-mypy: ## lint api python sources with mypy
	@echo 'lint:mypy started…'
	@$(COMPOSE_RUN_CLIENT) mypy qcc tests
.PHONY: lint-client-mypy


test: ## run all services tests
test: \
	test-api \
	test-client
.PHONY: test

test-api: ## run API tests
	SERVICE=api bin/pytest
.PHONY: test-api

test-client: ## run client tests
	SERVICE=client bin/pytest
.PHONY: test-client

# -- Misc
help:
	@grep -E '^[a-zA-Z0-9_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'
.PHONY: help
