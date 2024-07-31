# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Allow to configure `API_STATIQUE_PAGE_MAX_SIZE` and `API_STATIQUE_PAGE_SIZE`
  independently from `API_STATIQUE_BULK_CREATE_MAX_SIZE`
- Store french administrative levels and geographic boundaries (shapes)

### Changed

- Upgrade fastapi to `0.111.1`
- Upgrade geoalchemy2 to `0.15.2`
- Upgrade sentry-sdk to `2.10.0`
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

[unreleased]: https://github.com/MTES-MCT/qualicharge/compare/v0.10.0...main
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
