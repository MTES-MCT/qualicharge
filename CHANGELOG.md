# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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

[unreleased]: https://github.com/MTES-MCT/qualicharge/compare/v0.5.0...main
[0.5.0]: https://github.com/MTES-MCT/qualicharge/compare/v0.4.0...v0.5.0
[0.4.0]: https://github.com/MTES-MCT/qualicharge/compare/v0.3.0...v0.4.0
[0.3.0]: https://github.com/MTES-MCT/qualicharge/compare/v0.2.1...v0.3.0
[0.2.1]: https://github.com/MTES-MCT/qualicharge/compare/v0.2.0...v0.2.1
[0.2.0]: https://github.com/MTES-MCT/qualicharge/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/MTES-MCT/qualicharge/compare/dc6a9e2...v0.1.0
