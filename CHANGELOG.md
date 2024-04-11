# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Defined dynamic status model
- Defined `/statique` endpoints and models

### Changed

- Moved to `/whoami` endpoint to the `/auth` router

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

[unreleased]: https://github.com/MTES-MCT/qualicharge/compare/v0.2.1...main
[0.2.1]: https://github.com/MTES-MCT/qualicharge/compare/v0.2.0...v0.2.1
[0.2.0]: https://github.com/MTES-MCT/qualicharge/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/MTES-MCT/qualicharge/compare/dc6a9e2...v0.1.0
