# -- General
SHELL := /bin/bash

# -- Docker
COMPOSE                = bin/compose
COMPOSE_UP             = $(COMPOSE) up -d --force-recreate
COMPOSE_RUN            = $(COMPOSE) run --rm --no-deps
COMPOSE_RUN_API        = $(COMPOSE_RUN) api
COMPOSE_RUN_API_PIPENV = $(COMPOSE_RUN_API) pipenv run
COMPOSE_RUN_CLIENT     = $(COMPOSE_RUN) client

# -- Tools
CURL = $(COMPOSE_RUN) curl

# -- Ressources
AFIREV_CHARGING_DATASET_URL = https://afirev.fr/en/liste-des-identifiants-attribues/

# ==============================================================================
# RULES

default: help

# -- Files
data:
	mkdir -p data

data/afirev-charging.csv: data
	@echo "You should download CSV file from $(AFIREV_CHARGING_DATASET_URL)"

# -- Docker/compose
bootstrap: ## bootstrap the project for development
bootstrap: \
  build \
  migrate-api \
  create-api-test-db \
  create-metabase-db \
  seed-metabase \
  seed-oidc \
  create-superuser \
  jupytext--to-ipynb \
  seed-api
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

build-notebook: ## build custom jupyter notebook image
	@$(COMPOSE) build notebook
.PHONY: build-notebook

build-opendata: ## build opendata image
	@$(COMPOSE) build opendata
.PHONY: build-opendata

down: ## stop and remove all containers
	@$(COMPOSE) down
.PHONY: down

logs: ## display all services logs (follow mode)
	@$(COMPOSE) logs -f
.PHONY: logs

logs-api: ## display API server logs (follow mode)
	@$(COMPOSE) logs -f api
.PHONY: logs-api

logs-notebook: ## display notebook logs (follow mode)
	@$(COMPOSE) logs -f notebook
.PHONY: logs-notebook

logs-opendata: ## display opendata logs (follow mode)
	@$(COMPOSE) logs -f opendata
.PHONY: logs-opendata

run: ## run the api server (and dependencies)
	$(COMPOSE_UP) --wait api
.PHONY: run

run-all: ## run the whole stack
	$(COMPOSE_UP) api keycloak metabase notebook opendata
.PHONY: run-all

run-metabase: ## run the metabase service
	$(COMPOSE_UP) metabase
.PHONY: run-metabase

run-notebook: ## run the notebook service
	$(COMPOSE_UP) notebook
.PHONY: run-notebook

run-opendata: ## run the opendata service
	$(COMPOSE_UP) opendata
.PHONY: run-opendata

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

dump-metabase:  ## dump metabase objects
	bin/pg_dump -a --inserts \
		-t Report_Card \
		-t Report_Dashboard \
		-t Report_DashboardCard \
		-t Dashboard_Tab \
		-t Setting \
		-U qualicharge \
		metabaseappdb > src/metabase/custom.sql
.PHONY: dump-metabase

migrate-api:  ## run alembic database migrations for the api service
	@echo "Running api service database engine…"
	@$(COMPOSE_UP) --wait postgresql
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

jupytext--to-md: ## convert local ipynb files into md
	bin/jupytext --to md work/src/notebook/**/*.ipynb
.PHONY: jupytext--to-md

jupytext--to-ipynb: ## convert remote md files into ipynb
	bin/jupytext --to ipynb work/src/notebook/**/*.md
.PHONY: jupytext--to-ipynb

reset-db: ## Reset the PostgreSQL database
	$(COMPOSE) stop postgresql
	$(COMPOSE) down postgresql
	$(COMPOSE_UP) postgresql
	$(MAKE) migrate-api
	$(COMPOSE_UP) api
	$(MAKE) create-superuser
.PHONY: reset-db

seed-api: ## seed the API database (static data)
seed-api: run
	zcat data/irve-statique.json.gz | \
		bin/qcc static bulk --chunk-size 100
.PHONY: seed-api

seed-metabase: ## seed the Metabase server
	@echo "Running metabase service …"
	@$(COMPOSE_UP) --wait metabase
	@echo "Create metabase initial admin user…"
	bin/metabase-init
	@echo "Create API data source…"
	$(COMPOSE_RUN) terraform init
	$(COMPOSE_RUN) terraform apply -auto-approve
	cat src/metabase/custom.sql | \
	  bin/psql \
		  -U qualicharge \
		  -d metabaseappdb
.PHONY: seed-metabase

seed-oidc: ## seed the OIDC provider
	@echo 'Starting OIDC provider…'
	@$(COMPOSE_UP) keycloak
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
