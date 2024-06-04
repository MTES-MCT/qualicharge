# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Document API authentication flow
- Document API data schemas

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

[unreleased]: https://github.com/MTES-MCT/qualicharge/compare/v0.8.0...main
[0.8.0]: https://github.com/MTES-MCT/qualicharge/compare/v0.7.0...v0.8.0
[0.7.0]: https://github.com/MTES-MCT/qualicharge/compare/v0.6.0...v0.7.0
[0.6.0]: https://github.com/MTES-MCT/qualicharge/compare/v0.5.0...v0.6.0
[0.5.0]: https://github.com/MTES-MCT/qualicharge/compare/v0.4.0...v0.5.0
[0.4.0]: https://github.com/MTES-MCT/qualicharge/compare/v0.3.0...v0.4.0
[0.3.0]: https://github.com/MTES-MCT/qualicharge/compare/v0.2.1...v0.3.0
[0.2.1]: https://github.com/MTES-MCT/qualicharge/compare/v0.2.0...v0.2.1
[0.2.0]: https://github.com/MTES-MCT/qualicharge/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/MTES-MCT/qualicharge/compare/dc6a9e2...v0.1.0
