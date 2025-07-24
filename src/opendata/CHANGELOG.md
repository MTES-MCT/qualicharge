# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Configured Data7 0.12.0
- Use the `Statique` materialized view for the `statiques` dataset
- Integrate HTTP Basic Authentication using NGINX as a reverse-proxy

### Changed

- Use the `LatestStatus` cache table to speed up query performance

#### Dependencies

- Upgrade Psycopg to `3.2.9`
- Upgrade `urllib3` to `2.5.0`

[unreleased]: https://github.com/MTES-MCT/qualicharge/
