# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

#### Indicators

- Implement infrastructure indicators (t1, i1, i4, i7)
- Implement extract indicators (e4)
- Implement historicization (up)
- Implement usage indicators (u5, u6, u9, u10, u11, u12, u13)

#### Quality

- Integrate Great-Expectations
- Add static expectations
  - Stations (AFIE, AFIP, P50E, PDCL, POWU, POWL, CRDF)
  - Locations (INSE, ADDR, LOCP)
  - Power supply (PDLM, NE10)
  - Operator and owner (OPEM, AMEM)
- Add dynamic expectations
  - Sesssions (DUPS, OVRS, LONS, NEGS, FRES)
  - Energy (ENEU, ENEA, ENEX, ODUR)
- Update PDLM query

#### Cooling

- Extract old statuses

### Changed

- Upgrade API database to PG 15 / TimescaleDB 2.19
- Adjust level of historicization
- Update indicators table indexes

[unreleased]: https://github.com/MTES-MCT/qualicharge/
