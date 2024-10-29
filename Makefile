# -- General
SHELL := /bin/bash

# -- Docker
COMPOSE                    = bin/compose
COMPOSE_UP                 = $(COMPOSE) up -d
COMPOSE_RUN                = $(COMPOSE) run --rm --no-deps
COMPOSE_RUN_API            = $(COMPOSE_RUN) api
COMPOSE_RUN_API_PIPENV     = $(COMPOSE_RUN_API) pipenv run
COMPOSE_RUN_CLIENT         = $(COMPOSE_RUN) client
COMPOSE_RUN_PREFECT_PIPENV = $(COMPOSE_RUN) prefect pipenv run

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
  migrate-prefect \
  create-api-test-db \
  create-metabase-db \
  create-prefect-db \
  create-dashboard-db \
  migrate-dashboard-db \
  seed-metabase \
  seed-oidc \
  create-api-superuser \
  create-dashboard-superuser \
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

build-prefect: ## build prefect image
	@$(COMPOSE) build prefect
.PHONY: build-prefect

build-dashboard: ## build dashboard image
	@$(COMPOSE) build dashboard
.PHONY: build-dashboard

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

logs-prefect: ## display prefect logs (follow mode)
	@$(COMPOSE) logs -f prefect prefect-worker
.PHONY: logs-prefect

logs-dashboard: ## display dashboard logs (follow mode)
	@$(COMPOSE) logs -f dashboard
.PHONY: logs-dashboard

run: ## run the api server (and dependencies)
	$(COMPOSE_UP) --wait api
.PHONY: run

run-all: ## run the whole stack
	$(COMPOSE_UP) api keycloak metabase notebook opendata dashboard
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

run-prefect: ## run the prefect service
	$(COMPOSE_UP) --wait prefect
	$(COMPOSE_UP) prefect-worker
.PHONY: run-prefect

status: ## an alias for "docker compose ps"
	@$(COMPOSE) ps
.PHONY: status

stop: ## stop all servers
	@$(COMPOSE) stop
.PHONY: stop

# -- Provisioning
data/qualicharge-api-schema.sql:
	$(COMPOSE) exec postgresql pg_dump -s -Z 9 -U qualicharge -F c qualicharge-api > data/qualicharge-api-schema.sql

data/qualicharge-api-data.sql:
	$(COMPOSE) exec postgresql pg_dump -a -Z 9 -U qualicharge -F c qualicharge-api > data/qualicharge-api-data.sql

backup-api-db: ## create API database backup
backup-api-db: \
	data/qualicharge-api-schema.sql \
  data/qualicharge-api-data.sql
.PHONY: backup-api-db

restore-api-db-data: ## restore API database backup data
restore-api-db-data: data/qualicharge-api-data.sql
	cat data/qualicharge-api-data.sql | \
		$(COMPOSE) exec -T postgresql pg_restore -a -U qualicharge -F c -d qualicharge-api
.PHONY: restore-api-db-data

restore-api-db-schema: ## restore API database backup schema
restore-api-db-schema: data/qualicharge-api-schema.sql
	cat data/qualicharge-api-schema.sql | \
		$(COMPOSE) exec -T postgresql pg_restore -s -U qualicharge -F c -d qualicharge-api
.PHONY: restore-api-db-schema

restore-api-db: ## restore API database backup
restore-api-db: \
	restore-api-db-schema \
	restore-api-db-data
.PHONY: restore-api-db

create-api-test-db: ## create API test database
	@echo "Creating api service test database…"
	@$(COMPOSE) exec postgresql bash -c 'psql "postgresql://$${POSTGRES_USER}:$${POSTGRES_PASSWORD}@$${QUALICHARGE_DB_HOST}:$${QUALICHARGE_DB_PORT}/postgres" -c "create database \"$${QUALICHARGE_TEST_DB_NAME}\";"' || echo "Duly noted, skipping database creation."
	@$(COMPOSE) exec postgresql bash -c 'psql "postgresql://$${POSTGRES_USER}:$${POSTGRES_PASSWORD}@$${QUALICHARGE_DB_HOST}:$${QUALICHARGE_DB_PORT}/$${QUALICHARGE_TEST_DB_NAME}" -c "create extension postgis;"' || echo "Duly noted, skipping extension creation."
.PHONY: create-api-test-db

create-metabase-db: ## create metabase database
	@echo "Creating metabase service database…"
	@$(COMPOSE) exec postgresql bash -c 'psql "postgresql://$${POSTGRES_USER}:$${POSTGRES_PASSWORD}@$${QUALICHARGE_DB_HOST}:$${QUALICHARGE_DB_PORT}/postgres" -c "create database \"$${MB_DB_DBNAME}\";"' || echo "Duly noted, skipping database creation."
.PHONY: create-metabase-db

create-prefect-db: ## create prefect database
	@echo "Creating prefect service database…"
	@$(COMPOSE) exec postgresql bash -c 'psql "postgresql://$${POSTGRES_USER}:$${POSTGRES_PASSWORD}@$${QUALICHARGE_DB_HOST}:$${QUALICHARGE_DB_PORT}/postgres" -c "create database \"$${PREFECT_API_DATABASE_NAME}\";"' || echo "Duly noted, skipping database creation."
.PHONY: create-prefect-db

create-dashboard-db: ## create dashboard database
	@echo "Creating dashboard service database…"
	@$(COMPOSE) exec postgresql bash -c 'psql "postgresql://$${POSTGRES_USER}:$${POSTGRES_PASSWORD}@$${QUALICHARGE_DB_HOST}:$${QUALICHARGE_DB_PORT}/postgres" -c "create database \"$${DASHBOARD_DB_NAME}\";"' || echo "Duly noted, skipping database creation."
.PHONY: create-dashboard-db

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

drop-dashboard-db: ## drop dashboard database
	@echo "Droping dashboard service database…"
	@$(COMPOSE) exec postgresql bash -c 'psql "postgresql://$${POSTGRES_USER}:$${POSTGRES_PASSWORD}@$${QUALICHARGE_DB_HOST}:$${QUALICHARGE_DB_PORT}/postgres" -c "drop database \"$${DASHBOARD_DB_NAME}\";"' || echo "Duly noted, skipping database deletion."
.PHONY: drop-dashboard-db

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

migrate-dashboard-db: ## create dashboard database
	@echo "Running dashboard service database engine…"
	@$(COMPOSE_UP) --wait postgresql
	@echo "Migrating dashboard database…"#
	@bin/manage migrate
.PHONY: migrate-dashboard-db

create-api-superuser: ## create api super user
migrate-prefect:  ## run prefect database migrations
	@echo "Running prefect service database engine…"
	@$(COMPOSE_UP) --wait postgresql
	@echo "Running migrations for prefect service…"
	@$(COMPOSE_RUN_PREFECT_PIPENV) prefect server database upgrade -y
.PHONY: migrate-prefect

post-deploy-prefect:  ## run prefect post-deployment script
	@echo "Running prefect service…"
	@$(COMPOSE_UP) --wait prefect
	@echo "Running postdeploy script for prefect service…"
	@$(COMPOSE) exec prefect pipenv run honcho start postdeploy
.PHONY: post-deploy-prefect

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
.PHONY: create-api-superuser

create-dashboard-superuser: ## create dashboard super user
	@echo "Running dashboard service database engine…"
	@$(COMPOSE_UP) --wait postgresql
	@echo "Creating dashboard super user…"
	@bin/manage createsuperuser --noinput
.PHONY: create-dashboard-superuser

jupytext--to-md: ## convert local ipynb files into md
	bin/jupytext --to md work/src/notebook/**/*.ipynb
.PHONY: jupytext--to-md

jupytext--to-ipynb: ## convert remote md files into ipynb
	bin/jupytext --to ipynb work/src/notebook/**/*.md
.PHONY: jupytext--to-ipynb

reset-db: ## Reset the PostgreSQL database
	$(COMPOSE) stop
	$(COMPOSE) down postgresql metabase
	$(MAKE) migrate-api
	$(MAKE) create-api-superuser
	$(MAKE) create-api-test-db
	$(MAKE) create-metabase-db
	$(MAKE) seed-metabase
	$(MAKE) create-prefect-db
	$(MAKE) create-dashboard-db
	$(MAKE) migrate-dashboard-db
	$(MAKE) create-dashboard-superuser
	$(MAKE) migrate-prefect
.PHONY: reset-db

seed-api: ## seed the API database (static data)
seed-api: run
	zcat data/irve-statique.json.gz | \
		bin/qcc static bulk --chunk-size 1000
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
	lint-client \
	lint-prefect
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

lint-prefect: ## lint api python sources
lint-prefect: \
  lint-prefect-black \
  lint-prefect-ruff \
  lint-prefect-mypy
.PHONY: lint-prefect

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

lint-prefect-black: ## lint prefect python sources with black
	@echo 'lint:black started…'
	@$(COMPOSE_RUN_PREFECT_PIPENV) black indicators tests
.PHONY: lint-prefect-black

lint-prefect-ruff: ## lint prefect python sources with ruff
	@echo 'lint:ruff started…'
	@$(COMPOSE_RUN_PREFECT_PIPENV) ruff check indicators tests
.PHONY: lint-prefect-ruff

lint-prefect-ruff-fix: ## lint and fix prefect python sources with ruff
	@echo 'lint:ruff-fix started…'
	@$(COMPOSE_RUN_PREFECT_PIPENV) ruff check --fix indicators tests
.PHONY: lint-prefect-ruff-fix

lint-prefect-mypy: ## lint prefect python sources with mypy
	@echo 'lint:mypy started…'
	@$(COMPOSE_RUN_PREFECT_PIPENV) mypy indicators tests
.PHONY: lint-prefect-mypy

test: ## run all services tests
test: \
	test-api \
	test-client \
	test-prefect
.PHONY: test

test-api: ## run API tests
	SERVICE=api bin/pytest
.PHONY: test-api

test-client: ## run client tests
	SERVICE=client bin/pytest
.PHONY: test-client

test-prefect: ## run prefect tests
	SERVICE=prefect-test bin/pytest
.PHONY: test-prefect

# -- Misc
help:
	@grep -E '^[a-zA-Z0-9_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'
.PHONY: help
