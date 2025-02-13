# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- bootstrap dashboard project
- add custom user model
- add core app with Entity and DeliveryPoint models
- add consent app with Consent model
- add ProConnect authentication system
- add dashboard homepage
- add consent form to manage consents of one or many entities
- added a validated consent page allowing consultation of validated consent for the 
  current period.
- add an email notification to users (via Brevo) after they have validated their consents.
- add admin integration for Entity, DeliveryPoint and Consent
- add mass admin action (make revoked) for consents
- add validators for SIRET, NAF code and Zip code 
- disallow mass action "delete" for consents in admin
- block the updates of all new data if a consent has the status `REVOKED`
- block the updates of all new data if a consent has the status `VALIDATED`
- allow selected consent fields update if status changes from `VALIDATED` to  `REVOKED`
- block the deletion of consent if it has the status `VALIDATED` or `REVOKED` 
- block consent updates (via the consent form) if the consent status is not `AWAITING`
- integration of custom 403, 404 and 500 pages 
- sentry integration
- added a signal on the creation of a delivery point. This signal allows the creation 
of the consent corresponding to the delivery point


[unreleased]: https://github.com/MTES-MCT/qualicharge/compare/main...bootstrap-dashboard-project

