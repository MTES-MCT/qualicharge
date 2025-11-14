# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Changed

#### Dependencies

- Upgrade `anyio` to `4.10.0`
- Upgrade `Pydantic` to `2.12.4`
- Upgrade `pydantic-settings` to `2.12.0`
- Upgrade `typer` to `0.19.0`

### Fixed

- Fix copy/pasta in manage endpoint doc strings

## [0.3.0] - 2025-03-14

### Added

- Add support for new `/manage` API endpoints

### Changed

#### Dependencies

- Upgrade `anyio` to `4.6.1`
- Upgrade `httpx` to `0.28.0`
- Upgrade `Pydantic` to `2.9.1`
- Upgrade `pydantic-settings` to `2.8.1`
- Upgrade `typer` to `0.15.2`

## [0.2.0] - 2024-09-05

### Changed

- Compress requests for bulk endpoints

#### Dependencies

- Upgrade `Pydantic` to `2.7.4`
- Upgrade `pydantic-settings` to `2.8.0`
- Upgrade `typer` to `0.12.5`
- Upgrade `httpx` to `0.27.2`

## [0.1.0] - 2024-06-14

### Added

- Add `QCC` QualiCharge API client
- Add `qcc` CLI

[unreleased]: https://github.com/MTES-MCT/qualicharge/compare/v0.3.0-cli...main
[0.3.0]: https://github.com/MTES-MCT/qualicharge/releases/tag/v0.2.0-cli...v0.3.0-cli
[0.2.0]: https://github.com/MTES-MCT/qualicharge/releases/tag/v0.1.0-cli...v0.2.0-cli
[0.1.0]: https://github.com/MTES-MCT/qualicharge/releases/tag/v0.1.0-cli
