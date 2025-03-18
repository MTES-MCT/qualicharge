# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Add manage router and `station/siren` endpoint for the Dashboard

### Fixed

- Allow creating a new PDC the day it has been connected

## [0.19.1] - 2025-03-10

### Changed

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

- Upgrade fastapi to `0.115.5`
- Upgrade geoalchemy2 to `0.16.0`
- Upgrade pyjwt to `2.10.0`
- Upgrade setuptools to `75.5.0`
- Send DB query details on Statique API errors only in debug mode
- Move `num_pdl` field to a 64-chars string
- Return created objects UUIDs for statuses and sessions

## [0.14.0] - 2024-11-15

### Added

- Allow uvicorn workers configuration in start script using the
  `QUALICHARGE_UVICORN_WORKERS` environment variable
- Make database engine connections pool size configurable
  (`DB_CONNECTION_POOL_SIZE` and `DB_CONNECTION_MAX_OVERFLOW` settings)
- Add a `--json` flag to the `read-user` CLI command

### Changed

- Upgrade alembic to `1.14.0`
- Upgrade fastapi to `0.115.4`
- Upgrade pyarrow to `18.0.0`
- Upgrade pydantic-extras-types to `2.10.0`
- Upgrade pydantic-settings to `2.6.1`
- Upgrade pyinstrument to `5.0.0`
- Upgrade python-multipart to `0.0.17`
- Upgrade sentry-sdk to `2.18.0`
- Set fk to `NULL` when related table entry is deleted for the `Station` table

### Fixed

- Add missing City / Department table foreign key constraints

## [0.13.0] - 2024-10-11

### Changed

- Add geo-boundaries population and area fields
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
- Upgrade fastapi to `0.112.2`
- Upgrade typer to `0.12.5`
- Upgrade sqlmodel to `0.0.22`

## [0.11.0] - 2024-08-14

### Added

- Allow to configure `API_STATIQUE_PAGE_MAX_SIZE` and `API_STATIQUE_PAGE_SIZE`
  independently from `API_STATIQUE_BULK_CREATE_MAX_SIZE`
- Store french administrative levels and geographic boundaries (shapes)

### Changed

- Upgrade fastapi to `0.112.0`
- Upgrade geoalchemy2 to `0.15.2`
- Upgrade pydantic-settings to `2.4.0`
- Upgrade PyJWT to `2.9.0`
- Upgrade sentry-sdk to `2.13.0`
- Upgrade SQLModel to `0.0.21`
- Switched to Psycopg 3.x

### Fixed

- Add relevant data examples for Swagger
- Improve database session management
- `PointDeCharge.id_pdc_itinerance` should be unique

## [0.10.0] - 2024-07-01

### Changed

- API dynamique bulk requests now returns the number of created items
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

[unreleased]: https://github.com/MTES-MCT/qualicharge/compare/v0.19.1...main
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
