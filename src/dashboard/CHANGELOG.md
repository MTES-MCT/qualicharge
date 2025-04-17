# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Changed

#### Dependencies

- Upgrade `Django` to `5.2.2`
- Upgrade `jsonschema` to `4.24.0`
- Upgrade `requests` to `2.32.4`
- Upgrade `urllib3` to `2.5.0`

## [0.1.0] - 2025-05-07

### Added

- add `renewable` app with `Renewable` model
- add admin integration for `Renewable` model
- add `get_current_quarter_date_range` utility
- add `has_renewable` field to delivery points model
- add `python-dateutil`

## [Unreleased]

### Added

- bootstrap dashboard project
- add a base view combining mixins for consistency
- add dashboard homepage
- integrate custom 403, 404, and 500 error pages
- add API connector for the "Annuaire des Entreprises" API
- add API connector for the QualiCharge API
- add Sentry integration
- add custom user model
- add ProConnect authentication system
- add `UserValidationMixin` to ensure access restrictions for unvalidated users
- add a specific restricted view for unvalidated users
- add mass admin action to validate users
- add core app with `Entity` and `DeliveryPoint` models
- add admin integration for `Entity`, `DeliveryPoint` and `Station`
- add a helper function to sync delivery points and stations from the QualiCharge API
- add a helper function to retrieve company information from its SIRET using the
  "Annuaire des Entreprises" API
- add validators for SIRET, SIREN, NAF code and Zip code
- add a utility function to extract SIREN from a SIRET
- add the consent app with `Consent` model
- add a consent form to manage consents for a given entity
- add a consent form to manage upcoming consents
- add a validated consent page, allowing users to consult validated consents for the current period
- add admin integration for `Consent`
- add a mass admin action to "revoke" multiple consents
- allow selected consent fields to be updated when transitioning from the `VALIDATED`
  to the `REVOKED` status
- disallow the "delete" mass action on consents in admin
- disallow the updates of all new data if a consent has the status `REVOKED`
- disallow the updates of all new data if a consent has the status `VALIDATED`
- disallow the deletion of consent if it has the status `VALIDATED` or `REVOKED`
- disallow consent updates (via the consent form) if the consent status is not `AWAITING`
- add a signal upon creation of a delivery point to automatically create the corresponding consent.
- add a helper function to renew expiring consents
- add a helper function to create consents for delivery points with no active consents
- add Brevo integration to send mail
- add an email notification to admins upon new user creation
- add an email notification to users upon validation by an admin
- add en email notification to users with pending consents awaiting validation
- add an email notification to users after their consents have been validated
- add a command to sync delivery points from the QualiCharge API
- add a command to renew consents (duplicate expiring consents and generate new consents)
- add a command to notify users about their pending consents
- add a command to retrieve company information from its SIRET using the
  "Annuaire des Entreprises" API (for development only)
- add a command to seed consents (for development only)
- add cron job configuration to schedule management tasks

[unreleased]: https://github.com/MTES-MCT/qualicharge/compare/v0.1.0-dashboard...main
[0.1.0]: https://github.com/MTES-MCT/qualicharge/releases/tag/v0.1.0-dashboard
