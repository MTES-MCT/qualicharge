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
- add `UserValidationMixin` to ensure access restrictions for unvalidated users.
- add a base view combining mixins for consistency
- add dashboard homepage
- add consent form to manage consents of one entity
- add consent form to manage upcoming consents
- added a validated consent page allowing consultation of validated consent for the 
  current period.
- add an email notification to users (via Brevo) after they have validated their consents.
- add en email notification to users if they have awaiting consents.
- add admin integration for Entity, DeliveryPoint and Consent
- add mass admin action (make revoked) for consents
- add mass admin action to validate users
- add validators for SIRET, NAF code and Zip code 
- add API connector to the "Annuaire des Entreprises" API
- add API connector to the QualiCharge API
- add a command to sync delivery points from qualicharge API  
- add a signal on the creation of a delivery point. This signal allows the creation 
of the consent corresponding to the delivery point
- retrieve company information from its SIRET using the "Annuaire des Entreprises" API
- disallow mass action "delete" for consents in admin
- block the updates of all new data if a consent has the status `REVOKED`
- block the updates of all new data if a consent has the status `VALIDATED`
- allow selected consent fields update if status changes from `VALIDATED` to  `REVOKED`
- block the deletion of consent if it has the status `VALIDATED` or `REVOKED` 
- block consent updates (via the consent form) if the consent status is not `AWAITING`
- integration of custom 403, 404 and 500 pages 
- sentry integration


[unreleased]: https://github.com/MTES-MCT/qualicharge/compare/main...bootstrap-dashboard-project

