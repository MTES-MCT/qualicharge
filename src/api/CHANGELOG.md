# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Changed

- Update the list of active operational units

#### Dependencies

- Upgrade `alembic` to `1.17.0`
- Upgrade `cachetools` to `6.2.2`
- Upgrade `fastapi` to `0.121.2`
- Upgrade `psycopg` to `3.2.12`
- Upgrade `pyarrow` to `22.0.0`
- Upgrade `pydantic-settings` to `2.12.0`
- Upgrade `sentry-sdk` to `2.44.0`

### Fixed 

- Restore orphan stations cleanup

## [0.30.0] - 2025-10-31

### Changed

- Update the list of active operational units

#### Dependencies

- Upgrade `alembic` to `1.17.0`
- Upgrade `email-validator` to `2.3.0`
- Upgrade `fastapi` to `0.120.0`
- Upgrade `pandas` to `2.3.3`
- Upgrade `psycopg` to `3.2.11`
- Upgrade `pydantic-extra-types` to `2.10.6`
- Upgrade `pydantic-settings` to `2.11.0`
- Upgrade `questionary` to `2.1.1`
- Upgrade `sentry-sdk` to `2.42.1`
- Upgrade `sqlalchemy-utils` to `0.42.0`
- Upgrade `sqlmodel` to `0.0.27`
- Upgrade `typer` to `0.20.0`

## [0.29.0] - 2025-09-01

### Added

- Implement `PointDeCharge` and `Station` soft-delete [BC]
- Add new API endpoints for charge point (and station) decommissioning

### Changed

- Update the list of active operational units

#### Dependencies

- Upgrade `pandas` to `2.3.2`
- Upgrade `pyinstrument` to `5.1.1`
- Upgrade `sentry-sdk` to `2.35.0`
- Upgrade `typer` to `0.16.1`

## [0.28.0] - 2025-07-29

### Changed

- mark the following static fields as required:
  - `nom_amenageur`
  - `siren_amenageur`
  - `contact_amenageur`
  - `nom_operateur`
  - `telephone_operateur`

#### Dependencies

- Upgrade `FastAPI` to `0.116.1`
- Upgrade `geoalchemy2` to `0.18.0`
- Upgrade `pandas` to `2.3.1`
- Upgrade `pyarrow` to `21.0.0`
- Upgrade `sentry-sdk` to `2.33.2`

## [0.27.0] - 2025-07-16

### Added

- CLI: install a `qcm` script for management commands instead of using a module
  entrypoint (`python -m qualicharge`)
- CLI: implement add/remove operational units options to the `qcm groups
update` command
- CLI: add new `qcm ou list` command to explore operational units and related
  groups

### Changed

- Move CLI commands to grouped sub-commands for `users`, `groups` and `statics`
- Switched to UV package manager

#### Dependencies

- Upgrade `FastAPI` to `0.115.14`
- Upgrade `geopandas` to `1.1.1`
- Upgrade `pydantic-settings` to `2.10.1`
- Upgrade `sentry-sdk` to `2.32.0`

## [0.26.0] - 2025-07-01

### Added

- Implement latest status cache in the `LatestStatus` table

### Changed

- Improve bulk importation error message

### Fixed

- Fix same address / different location bulk importation

## [0.25.0] - 2025-06-20

### Added

- Add a configurable retention policy for `Status` and `Session` data
- Create new database indexes:
  - `ix_pointdecharge_station_id`
  - `ix_station_amenageur_id`
  - `ix_station_operateur_id`

### Changed

- Update the list of active operational units

#### Dependencies

- Upgrade `alembic` to `1.16.2`
- Upgrade `cachetools` to `6.1.0`
- Upgrade `FastAPI` to `0.115.13`
- Upgrade `Pydantic` to `2.11.7`
- Upgrade `pydantic-settings` to `2.10.0`
- Upgrade `sentry-sdk` to `2.30.0`
- Upgrade `urllib3` to `2.5.0`

### Removed

- Drop database indexes:
  - `status_horodatage_idx`
  - `ix_status_horodatage_pdc_id`
  - `session_start_idx`
  - `ix_session_start_pdc_id`

## [0.24.0] - 2025-06-11

### Added

- Clean activity table every day using a cronjob

### Fixed

- Update `id_station_itinerance` field examples in the swagger documentation

### Changed

- `Statique` model string fields are now stripped
- `Statique.restriction_gabarit` field should be at least 2 characters long
- Update the list of active operational units (twice)

#### Dependencies

- Upgrade `alembic` to `1.16.1`
- Upgrade `cachetools` to `6.0.0`
- Upgrade `geopandas` to `1.1.0`
- Upgrade `pandas` to `2.3.0`
- Upgrade `psycopg` to `3.2.9`
- Upgrade `pydantic` to `2.11.5`
- Upgrade `pyinstrument` to `5.0.2`
- Upgrade `sentry-sdk` to `2.29.0`
- Upgrade `setuptools` to `80.9.0`
- Upgrade `typer` to `0.16.0`

## [0.23.0] - 2025-04-30

### Added

- Introduce two new database connection settings:
  - `DB_CONNECTION_POOL_CHECK`
  - `DB_CONNECTION_POOL_RECYCLE`

### Changed

#### Dependencies

- Upgrade `pyarrow` to `20.0.0`
- Upgrade `pydantic` to `2.11.3`
- Upgrade `pydantic-extra-types` to `2.10.4`
- Upgrade `pydantic-settings` to `2.9.1`
- Upgrade `sentry-sdk` to `2.27.0`
- Upgrade `setuptools` to `80.0.0`

## [0.22.1] - 2025-04-17

### Fixed

- Switch `Session` table to a TimescaleDB hypertable

## [0.22.0] - 2025-04-17

### Added

- Clean database static orphan entries using a SQL script ran as a cronjob task

### Changed

- Add time and fk-related missing database indexes for status & session tables
- Docs: update data schema restrictions
- Docs: add usage section

### Fixed

- Switch `Status` table to a TimescaleDB hypertable

## [0.21.0] - 2025-04-11

### Changed

- Update the list of active operational units

#### Dependencies

- Upgrade alembic to `1.15.2`
- Upgrade fastapi to `0.115.12`
- Upgrade psycopg to `3.2.6`
- Upgrade pydantic to `2.11.1`
- Upgrade pydantic-extra-types to `2.10.3`
- Upgrade sentry-sdk to `2.25.0`
- Upgrade setuptools to `78.1.0`

### Fixed

- Update `Localisation` discriminating field to `coordonneesXY` for
  statique-related helpers

## [0.20.0] - 2025-03-19

### Added

- Add manage router and `station/siren` endpoint for the Dashboard

### Fixed

- Allow creating a new PDC the day it has been connected
- Ignore stations without PDL in stations mananagement endpoint

## [0.19.1] - 2025-03-10

### Changed

#### Dependencies

- Upgrade alembic to `1.15.1`
- Upgrade fastapi to `0.115.11`
- Upgrade pydantic-settings to `2.8.1`
- Upgrade sqlmodel to `0.0.24`
- Upgrade typer to `0.15.2`

### Fixed

- Add default `None` value to API models optional fields or else they are
  considered as required

## [0.19.0] - 2025-02-25

### Added

- Implement a new `/dynamique/session/check` endpoint to check if a target
  session exists or not

### Changed

- Improve bulk endpoints documentation
- Improve `/dynamique` (bulk) create endpoint performance by using background
  tasks

#### Dependencies

- Upgrade cachetools to `5.5.2`
- Upgrade geoalchemy2 to `0.17.1`
- Upgrade psycopg to `3.2.5`
- Upgrade pyarrow to `19.0.1`
- Upgrade pydantic-settings to `2.8.0`
- Upgrade sentry-sdk to `2.22.0`

## [0.18.0] - 2025-02-10

### Added

- Integrate `postgresql_audit` for critical database changes versioning

### Changed

- Update the list of active operational units

#### Dependencies

- Upgrade fastapi to `0.115.8`
- Upgrade pydantic to `2.10.6`
- Upgrade pyinstrument to `5.0.1`

## [0.17.0] - 2025-01-29

### Added

- Activate and configure Sentry profiling by setting the
  `SENTRY_PROFILES_SAMPLE_RATE` configuration
- Set request's user (`username`) in Sentry's context
- Add `Localisation.coordonneesXY` unique contraint [BC] 💥
- Implement `Statique` materialized view

### Changed

- Prefetch user-related groups and operational units in `get_user` dependency
- Improve bulk endpoints permissions checking
- Cache logged user object for `API_GET_USER_CACHE_TTL` seconds to decrease the
  number of database queries
- CLI: sort groups and operational units alphabetically in the `list-groups`
  command
- Decrease the number of database queries for dynamic endpoints
- Cache the "get PointDeCharge id from its `id_pdc_itinerance`" database query
- Improve JSON string parsing using pyarrow engine
- Add default values for optional Statique model fields
- Migrate database enum types from names to values
- Improve API performance by integrating the `Statique` materialized view

#### Dependencies

- Upgrade alembic to `1.14.1`
- Upgrade geoalchemy2 to `0.17.0`
- Upgrade psycopg to `3.2.4`
- Upgrade pyarrow to `19.0.0`
- Upgrade pydantic to `2.10.5`
- Upgrade pydantic-extra-types to `2.10.2`
- Upgrade pydantic-settings to `2.7.1`
- Upgrade python-multipart to `0.0.20`
- Upgrade questionary to `2.1.0`
- Upgrade sentry-sdk to `2.20.0`

### Fixed

- Rename database `raccordementemum` to `raccordementenum`
- Run database migrations in a post-deploy hook

### Removed

- Remove `Localisation.adresse_station` unique constraint

## [0.16.0] - 2024-12-12

### Changed

#### Dependencies

- Upgrade fastapi to `0.115.6`
- Upgrade httpx to `0.28.1`
- Upgrade pyarrow to `18.1.0`
- Upgrade pydantic to `2.10.3`
- Upgrade pydantic-extra-types `2.10.1`
- Upgrade python-multipart to `0.0.19`
- Upgrade sentry-sdk to `2.19.2`
- Upgrade typer to `0.15.1`

### Fixed

- Allow `date_maj` field to be set to "today"
- Forbid `/static/` POST usage for an existing PDC

## [0.15.0] - 2024-11-21

### Changed

- Send DB query details on Statique API errors only in debug mode
- Move `num_pdl` field to a 64-chars string
- Return created objects UUIDs for statuses and sessions

#### Dependencies

- Upgrade fastapi to `0.115.5`
- Upgrade geoalchemy2 to `0.16.0`
- Upgrade pyjwt to `2.10.0`
- Upgrade setuptools to `75.5.0`

## [0.14.0] - 2024-11-15

### Added

- Allow uvicorn workers configuration in start script using the
  `QUALICHARGE_UVICORN_WORKERS` environment variable
- Make database engine connections pool size configurable
  (`DB_CONNECTION_POOL_SIZE` and `DB_CONNECTION_MAX_OVERFLOW` settings)
- Add a `--json` flag to the `read-user` CLI command

### Changed

- Set fk to `NULL` when related table entry is deleted for the `Station` table

#### Dependencies

- Upgrade alembic to `1.14.0`
- Upgrade fastapi to `0.115.4`
- Upgrade pyarrow to `18.0.0`
- Upgrade pydantic-extras-types to `2.10.0`
- Upgrade pydantic-settings to `2.6.1`
- Upgrade pyinstrument to `5.0.0`
- Upgrade python-multipart to `0.0.17`
- Upgrade sentry-sdk to `2.18.0`

### Fixed

- Add missing City / Department table foreign key constraints

## [0.13.0] - 2024-10-11

### Changed

- Add geo-boundaries population and area fields

#### Dependencies

- Upgrade alembic to `1.13.3`
- Upgrade fastapi to `0.115.0`
- Upgrade pandas to `2.2.3`
- Upgrade Psycopg to `3.2.3`
- Upgrade Pydantic to `2.9.1`
- Upgrade pydantic-settings to `2.5.2`
- Upgrade pyinstrument to `4.7.3`
- Upgrade python-multipart to `0.0.12`
- Upgrade sentry-sdk to `2.16.0`

### Fixed

- Migrate administrative boundaries tables schema and data

## [0.12.1] - 2024-09-09

### Fixed

- Commit `/statique/bulk` database transaction

## [0.12.0] - 2024-09-05

### Added

- Implement GZip requests support (mostly for bulk endpoints)
- Implement Pandas-based `StatiqueImporter`
- CLI: add `import-statique` command

### Changed

- Require the `code_insee_commune` field in both the `Statique` model and the
  `Localisation` schema
- Allow to submit a single item in bulk endpoints
- Add create or update support for the `/statique/bulk` endpoints (with improved
  performances)

#### Dependencies

- Upgrade fastapi to `0.112.2`
- Upgrade typer to `0.12.5`
- Upgrade sqlmodel to `0.0.22`

## [0.11.0] - 2024-08-14

### Added

- Allow to configure `API_STATIQUE_PAGE_MAX_SIZE` and `API_STATIQUE_PAGE_SIZE`
  independently from `API_STATIQUE_BULK_CREATE_MAX_SIZE`
- Store french administrative levels and geographic boundaries (shapes)

### Changed

- Switched to Psycopg 3.x

#### Dependencies

- Upgrade fastapi to `0.112.0`
- Upgrade geoalchemy2 to `0.15.2`
- Upgrade pydantic-settings to `2.4.0`
- Upgrade PyJWT to `2.9.0`
- Upgrade sentry-sdk to `2.13.0`
- Upgrade SQLModel to `0.0.21`

### Fixed

- Add relevant data examples for Swagger
- Improve database session management
- `PointDeCharge.id_pdc_itinerance` should be unique

## [0.10.0] - 2024-07-01

### Changed

- API dynamique bulk requests now returns the number of created items

#### Dependencies

- Upgrade alembic to `1.13.2`
- Upgrade Pydantic to `2.7.4`
- Upgrade pydantic-settings to `2.3.4`
- Upgrade pydantic-extra-types to `2.8.2`
- Upgrade email-validator to `2.2.0`
- Upgrade sentry-sdk to `2.7.1`

## [0.9.0] - 2024-06-11

### Added

- Document API authentication flow
- Document API data schemas

### Changed

#### Dependencies

- Upgrade `pydantic-extra-types` to `2.8.0`
- Upgrade `pydantic-settings` to `2.3.1`
- Upgrade `sentry-sdk` to `2.5.1`
- Upgrade `sqlmodel` to `0.0.19`

### Fixed

- Improve database transactions in statique endpoints
- Allow to update all statique-related model fields

## [0.8.0] - 2024-05-31

### Added

- Track user last login date time

### Changed

- CLI: remove the scopes column from the `list-users` command
- CLI: the `username` parameter is now required for the `create-user` command
- CLI: add the `read-user` command

### Fixed

- CLI: fix `create-user` command failure when no group exists (#70)

## [0.7.0] - 2024-05-30

### Added

- Integrate Sentry
- Manage users and groups using a new CLI

### Security

- Switch from `python-jose` to `PyJWT` as the
  [CVE-2022-29217](https://github.com/advisories/GHSA-ffqj-6fqr-9h24) does not
  seem to be fixed

## [0.6.0] - 2024-05-28

### Added

- Implement `OperationalUnit` schema
- Link `OperationalUnit` to `Station` using AFIREV prefixes
- Implement `User` and `Group` schemas
- Implement `User` scopes (fine-tuned permissions)
- Implement row permissions on API endpoints (given assigned operational units)
- Integrate OAuth2 password flow authentication fallback when OIDC is not
  enabled

## [0.5.0] - 2024-05-15

### Added

- Implement statique router endpoints
- Draft dynamique database schemas
- Implement dynamique router endpoints

### Changed

- Switch to TimescaleDB

#### Dependencies

- Upgrade FastAPI to 0.111.0

## [0.4.0] - 2024-04-23

### Added

- Implement static data database schemas

### Fixed

- Mark Static.id_pdc_itinerance field as required

## [0.3.0] - 2024-04-11

### Added

- Define `/dynamique` endpoints
- Define dynamic status and session models
- Define `/statique` endpoints and models

### Changed

- Move the `/whoami` endpoint to the `/auth` router

## [0.2.1] - 2024-04-08

### Fixed

- Add a custom exception handler for authentication failures

## [0.2.0] - 2024-04-05

### Added

- Integrate OIDC support
- Integrate PostgreSQL database persistency in an asynchronous context

## [0.1.0] - 2024-03-26

### Added

- Implement base FastAPI app

[unreleased]: https://github.com/MTES-MCT/qualicharge/compare/v0.30.0...main
[0.30.0]: https://github.com/MTES-MCT/qualicharge/compare/v0.29.0...v0.30.0
[0.29.0]: https://github.com/MTES-MCT/qualicharge/compare/v0.28.0...v0.29.0
[0.28.0]: https://github.com/MTES-MCT/qualicharge/compare/v0.27.0...v0.28.0
[0.27.0]: https://github.com/MTES-MCT/qualicharge/compare/v0.26.0...v0.27.0
[0.26.0]: https://github.com/MTES-MCT/qualicharge/compare/v0.25.0...v0.26.0
[0.25.0]: https://github.com/MTES-MCT/qualicharge/compare/v0.24.0...v0.25.0
[0.24.0]: https://github.com/MTES-MCT/qualicharge/compare/v0.23.0...v0.24.0
[0.23.0]: https://github.com/MTES-MCT/qualicharge/compare/v0.22.1...v0.23.0
[0.22.1]: https://github.com/MTES-MCT/qualicharge/compare/v0.22.0...v0.22.1
[0.22.0]: https://github.com/MTES-MCT/qualicharge/compare/v0.21.0...v0.22.0
[0.21.0]: https://github.com/MTES-MCT/qualicharge/compare/v0.20.0...v0.21.0
[0.20.0]: https://github.com/MTES-MCT/qualicharge/compare/v0.19.1...v0.20.0
[0.19.1]: https://github.com/MTES-MCT/qualicharge/compare/v0.19.0...v0.19.1
[0.19.0]: https://github.com/MTES-MCT/qualicharge/compare/v0.18.0...v0.19.0
[0.18.0]: https://github.com/MTES-MCT/qualicharge/compare/v0.17.0...v0.18.0
[0.17.0]: https://github.com/MTES-MCT/qualicharge/compare/v0.16.0...v0.17.0
[0.16.0]: https://github.com/MTES-MCT/qualicharge/compare/v0.15.0...v0.16.0
[0.15.0]: https://github.com/MTES-MCT/qualicharge/compare/v0.14.0...v0.15.0
[0.14.0]: https://github.com/MTES-MCT/qualicharge/compare/v0.13.0...v0.14.0
[0.13.0]: https://github.com/MTES-MCT/qualicharge/compare/v0.12.1...v0.13.0
[0.12.1]: https://github.com/MTES-MCT/qualicharge/compare/v0.12.0...v0.12.1
[0.12.0]: https://github.com/MTES-MCT/qualicharge/compare/v0.11.0...v0.12.0
[0.11.0]: https://github.com/MTES-MCT/qualicharge/compare/v0.10.0...v0.11.0
[0.10.0]: https://github.com/MTES-MCT/qualicharge/compare/v0.9.0...v0.10.0
[0.9.0]: https://github.com/MTES-MCT/qualicharge/compare/v0.8.0...v0.9.0
[0.8.0]: https://github.com/MTES-MCT/qualicharge/compare/v0.7.0...v0.8.0
[0.7.0]: https://github.com/MTES-MCT/qualicharge/compare/v0.6.0...v0.7.0
[0.6.0]: https://github.com/MTES-MCT/qualicharge/compare/v0.5.0...v0.6.0
[0.5.0]: https://github.com/MTES-MCT/qualicharge/compare/v0.4.0...v0.5.0
[0.4.0]: https://github.com/MTES-MCT/qualicharge/compare/v0.3.0...v0.4.0
[0.3.0]: https://github.com/MTES-MCT/qualicharge/compare/v0.2.1...v0.3.0
[0.2.1]: https://github.com/MTES-MCT/qualicharge/compare/v0.2.0...v0.2.1
[0.2.0]: https://github.com/MTES-MCT/qualicharge/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/MTES-MCT/qualicharge/compare/dc6a9e2...v0.1.0
