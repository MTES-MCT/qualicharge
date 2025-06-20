# -- General
SHELL := /bin/bash

# -- Docker
COMPOSE                    	 = bin/compose
COMPOSE_UP                 	 = $(COMPOSE) up -d --remove-orphans
COMPOSE_RUN                	 = $(COMPOSE) run --rm --no-deps
COMPOSE_RUN_API            	 = $(COMPOSE_RUN) api
COMPOSE_RUN_API_PIPENV     	 = $(COMPOSE_RUN_API) pipenv run
COMPOSE_RUN_CLIENT         	 = $(COMPOSE_RUN) client
COMPOSE_RUN_PREFECT_PIPENV 	 = $(COMPOSE_RUN) prefect pipenv run
COMPOSE_RUN_DASHBOARD_PIPENV = $(COMPOSE_RUN) dashboard pipenv run

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
bench-reset-db: ## Reset API database to run benchmark
	$(COMPOSE) stop
	$(COMPOSE) up -d --wait --force-recreate postgresql
	$(MAKE) migrate-api
	$(MAKE) create-api-superuser
	$(COMPOSE) up -d --wait api
	zcat data/irve-statique.json.gz | head -n 500 | \
		bin/qcc static bulk --chunk-size 1000
.PHONY: bench-reset-db

bench: ## run API benchmark
	$(COMPOSE_RUN_API_PIPENV) \
		locust \
		  -f /mnt/bench/locustfile.py \
			--headless \
			-u 30 \
			-r 1 \
			--run-time 30s \
			-H 'http://api:8000/api/v1' \
			--csv bench_admin \
			APIAdminUser
.PHONY: bench

bootstrap: ## bootstrap the project for development
bootstrap: \
  build \
  migrate-api \
  create-api-test-db \
  create-metabase-db \
  create-prefect-db \
  migrate-prefect \
  create-dashboard-db \
  migrate-dashboard \
  seed-metabase \
  seed-minio \
  seed-oidc \
  create-api-superuser \
  create-dashboard-superuser \
  seed-dashboard \
  jupytext--to-ipynb \
  run-api \
  seed-api \
  post-deploy-prefect
.PHONY: bootstrap

bootstrap-api: ## bootstrap the api service
bootstrap-api: \
  build-api \
  build-client \
  migrate-api \
  create-api-test-db \
  create-api-superuser \
  run-api \
  seed-api \
  refresh-api-static
.PHONY: bootstrap-api

bootstrap-dashboard: ## bootstrap the dashboard project for development
bootstrap-dashboard: \
  build-dashboard \
  reset-dashboard-db
.PHONY: bootstrap-dashboard

build: ## build services image
	$(COMPOSE) build
.PHONY: build

build-api: ## build the api image
	$(COMPOSE) build api
.PHONY: build-api

build-client: ## build the client image
	$(COMPOSE) build client
.PHONY: build-client

build-locust: ## build locust image
	@$(COMPOSE) build locust
.PHONY: build-locust

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

run-api: ## run the api server (and dependencies)
	$(COMPOSE_UP) --wait api
.PHONY: run-api

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

run-dashboard: ## run the dashboard service
	$(COMPOSE_UP) dashboard
.PHONY: run-dashboard

run-locust: ## run the locust service
	$(COMPOSE_UP) --wait locust-worker
.PHONY: run-locust

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
	$(COMPOSE) exec postgresql pg_dump -a -Z 9 -U qualicharge -F c qualicharge-api --exclude-table-data=activity > data/qualicharge-api-data.sql

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
	@$(COMPOSE) exec postgresql bash -c 'psql "postgresql://$${POSTGRES_USER}:$${POSTGRES_PASSWORD}@$${QUALICHARGE_DB_HOST}:$${QUALICHARGE_DB_PORT}/$${QUALICHARGE_TEST_DB_NAME}" -c "create extension btree_gist;"' || echo "Duly noted, skipping extension creation."
.PHONY: create-api-test-db

create-metabase-db: ## create metabase database
	@echo "Creating metabase service database…"
	@$(COMPOSE) exec postgresql bash -c 'psql "postgresql://$${POSTGRES_USER}:$${POSTGRES_PASSWORD}@$${QUALICHARGE_DB_HOST}:$${QUALICHARGE_DB_PORT}/postgres" -c "create database \"$${MB_DB_DBNAME}\";"' || echo "Duly noted, skipping database creation."
.PHONY: create-metabase-db

create-prefect-db: ## create prefect database
	@echo "Creating prefect service database…"
	@$(COMPOSE) exec postgresql bash -c 'psql "postgresql://$${POSTGRES_USER}:$${POSTGRES_PASSWORD}@$${QUALICHARGE_DB_HOST}:$${QUALICHARGE_DB_PORT}/postgres" -c "create database \"$${PREFECT_API_DATABASE_NAME}\";"' || echo "Duly noted, skipping database creation."
	@$(COMPOSE) exec postgresql bash -c 'psql "postgresql://$${POSTGRES_USER}:$${POSTGRES_PASSWORD}@$${QUALICHARGE_DB_HOST}:$${QUALICHARGE_DB_PORT}/postgres" -c "create database \"$${QUALICHARGE_INDICATORS_DB_NAME}\";"' || echo "Duly noted, skipping database creation."
.PHONY: create-prefect-db

create-dashboard-db: ## create dashboard database
	@echo "Running dashboard service database engine…"
	@$(COMPOSE_UP) --wait postgresql
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

drop-prefect-db: ## drop prefect database
	@echo "Droping prefect service database…"
	@$(COMPOSE) exec postgresql bash -c 'psql "postgresql://$${POSTGRES_USER}:$${POSTGRES_PASSWORD}@$${QUALICHARGE_DB_HOST}:$${QUALICHARGE_DB_PORT}/postgres" -c "drop database \"$${PREFECT_API_DATABASE_NAME}\";"' || echo "Duly noted, skipping database deletion."
	@$(COMPOSE) exec postgresql bash -c 'psql "postgresql://$${POSTGRES_USER}:$${POSTGRES_PASSWORD}@$${QUALICHARGE_DB_HOST}:$${QUALICHARGE_DB_PORT}/postgres" -c "drop database \"$${QUALICHARGE_INDICATORS_DB_NAME}\";"' || echo "Duly noted, skipping database deletion."
.PHONY: drop-prefect-db

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
	@$(COMPOSE) exec postgresql bash -c 'psql "postgresql://$${POSTGRES_USER}:$${POSTGRES_PASSWORD}@$${QUALICHARGE_DB_HOST}:$${QUALICHARGE_DB_PORT}/$${QUALICHARGE_DB_NAME}" -c "create extension btree_gist;"' || echo "Duly noted, skipping extension creation."
	@echo "Running migrations for api service…"
	@bin/alembic upgrade head
.PHONY: migrate-api

migrate-dashboard: ## create dashboard database
	@echo "Running dashboard service database engine…"
	@$(COMPOSE_UP) --wait postgresql
	@echo "Migrating dashboard database…"#
	@bin/manage migrate
.PHONY: migrate-dashboard

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
	@echo "Creating all deployments…"
	@$(COMPOSE) exec -T prefect pipenv run ./prefect-deploy-all.sh
.PHONY: post-deploy-prefect

create-api-superuser: ## create api super user
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
reset-db: \
  reset-api-db \
  create-prefect-db \
  migrate-prefect \
  create-metabase-db \
  seed-metabase \
  reset-dashboard-db
.PHONY: reset-db

refresh-api-static: ## Refresh the API Statique Materialized View
	$(COMPOSE) exec api pipenv run python -m qualicharge refresh-static
.PHONY: refresh-api-static

reset-api-db: ## Reset the PostgreSQL API database
	$(COMPOSE) stop
	$(COMPOSE) down postgresql
	$(COMPOSE_UP) --wait --force-recreate -d postgresql
	$(MAKE) migrate-api
	$(COMPOSE_UP) --wait --force-recreate -d api
	$(MAKE) create-api-superuser
	$(MAKE) create-api-test-db
.PHONY: reset-api-db

reset-dashboard-db: ## Reset the PostgreSQL dashboard database
	$(MAKE) create-dashboard-db
	$(MAKE) migrate-dashboard
	$(MAKE) create-dashboard-superuser
	$(MAKE) seed-dashboard
.PHONY: reset-dashboard-db

seed-api-static: ## seed the API database (static data)
	@echo "Creating statique database entries …"
	zcat data/irve-statique.json.gz | \
		bin/qcc static bulk --chunk-size 1000
.PHONY: seed-api-static

seed-api-statuses: ## seed the API database (status data)
	@echo "Creating status database entries …"
	zcat data/irve-dynamique-statuses.json.gz | \
		bin/qcc status bulk --chunk-size 1000
.PHONY: seed-api-statuses

seed-api-sessions: ## seed the API database (sessions data)
	@echo "Creating session database entries …"
	zcat data/irve-dynamique-sessions.json.gz | \
		bin/qcc session bulk --chunk-size 1000
.PHONY: seed-api-sessions

seed-api: ## seed the API database (static + dynamic data)
seed-api: \
  seed-api-static \
  refresh-api-static \
  seed-api-sessions \
  seed-api-statuses
.PHONY: seed-api

seed-metabase: ## seed the Metabase server
	@echo "Running metabase service …"
	@$(COMPOSE_UP) --wait --force-recreate metabase
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

seed-minio: ## seed the Minio server
	@echo "Running minio service …"
	@$(COMPOSE_UP) --wait minio
	@echo "Create Minio user and buckets…"
	@$(COMPOSE) exec minio /opt/bin/minio-init
.PHONY: seed-minio

seed-oidc: ## seed the OIDC provider
	@echo 'Starting OIDC provider…'
	@$(COMPOSE_UP) keycloak
	@$(COMPOSE_RUN) dockerize -wait http://keycloak:8080 -timeout 60s
	@echo 'Seeding OIDC client…'
	@$(COMPOSE) exec keycloak /usr/local/bin/kc-init
.PHONY: seed-oidc

seed-dashboard: ## seed dashboard
	@echo "Running dashboard service database engine…"
	@$(COMPOSE_UP) --wait postgresql
	@echo "Seeding dashboard…"
	@bin/manage loaddata dashboard/fixtures/dsfr_fixtures.json
	@bin/manage seed_consent
	@bin/manage seed_renewable
.PHONY: seed-dashboard

# -- API
lint: ## lint all sources
lint: \
	lint-api \
	lint-bench \
	lint-client \
	lint-prefect \
	lint-dashboard
.PHONY: lint

lint-api: ## lint api python sources
lint-api: \
  lint-api-black \
  lint-api-ruff \
  lint-api-mypy
.PHONY: lint-api

lint-bench: ## lint api python sources
lint-bench: \
  lint-bench-black \
  lint-bench-ruff \
  lint-bench-mypy
.PHONY: lint-bench

lint-client: ## lint client python sources
lint-client: \
  lint-client-black \
  lint-client-ruff \
  lint-client-mypy
.PHONY: lint-client

lint-prefect: ## lint prefect python sources
lint-prefect: \
  lint-prefect-black \
  lint-prefect-ruff \
  lint-prefect-mypy
.PHONY: lint-prefect

lint-dashboard: ## lint dashboard python sources
lint-dashboard: \
  lint-dashboard-black \
  lint-dashboard-ruff \
  lint-dashboard-mypy \
  lint-dashboard-djlint
.PHONY: lint-dashboard

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

lint-bench-black: ## lint bench python sources with black
	@echo 'lint:black started…'
	@$(COMPOSE_RUN_API_PIPENV) black /mnt/bench
.PHONY: lint-bench-black

lint-bench-ruff: ## lint bench python sources with ruff
	@echo 'lint:ruff started…'
	@$(COMPOSE_RUN_API_PIPENV) ruff check /mnt/bench
.PHONY: lint-bench-ruff

lint-bench-ruff-fix: ## lint and fix api python sources with ruff
	@echo 'lint:ruff-fix started…'
	@$(COMPOSE_RUN_API_PIPENV) ruff check --fix /mnt/bench
.PHONY: lint-bench-ruff-fix

lint-bench-mypy: ## lint bench python sources with mypy
	@echo 'lint:mypy started…'
	@$(COMPOSE_RUN_API_PIPENV) mypy /mnt/bench
.PHONY: lint-bench-mypy

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

lint-dashboard-black: ## lint dashboard python sources with black
	@echo 'lint:black dashboard started…'
	@$(COMPOSE_RUN_DASHBOARD_PIPENV) black dashboard apps tests
.PHONY: lint-dashboard-black

lint-dashboard-ruff: ## lint dashboard python sources with ruff
	@echo 'lint:ruff dashboard started…'
	@$(COMPOSE_RUN_DASHBOARD_PIPENV) ruff check dashboard apps tests
.PHONY: lint-dashboard-ruff

lint-dashboard-ruff-fix: ## lint and fix dashboard python sources with ruff
	@echo 'lint:ruff-fix dashboard started…'
	@$(COMPOSE_RUN_DASHBOARD_PIPENV) ruff check --fix dashboard apps tests
.PHONY: lint-dashboard-ruff-fix

lint-dashboard-mypy: ## lint dashboard python sources with mypy
	@echo 'lint:mypy dashboard started…'
	@$(COMPOSE_RUN_DASHBOARD_PIPENV) mypy dashboard apps tests
.PHONY: lint-dashboard-mypy

lint-dashboard-djlint: ## lint dashboard html sources with djlint
	@echo 'lint:djlint dashboard started…'
	@$(COMPOSE_RUN_DASHBOARD_PIPENV) djlint -
.PHONY: lint-dashboard-djlint

lint-dashboard-djlint-reformat: ## lint and reformat dashboard html sources with djlint
	@echo 'lint:djlint-reformat dashboard started…'
	@$(COMPOSE_RUN_DASHBOARD_PIPENV) djlint - --reformat
.PHONY: lint-dashboard-djlint-reformat

test: ## run all services tests
test: \
	test-api \
	test-client \
	test-prefect \
	test-dashboard
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

test-dashboard: ## run dashboard tests
	@echo "Run dashboard tests…"
	SERVICE=dashboard bin/pytest
.PHONY: test-dashboard

# -- Misc
help:
	@grep -E '^[a-zA-Z0-9_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'
.PHONY: help
