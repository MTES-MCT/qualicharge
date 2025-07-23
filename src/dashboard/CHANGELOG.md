# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Changed

#### Dependencies

- Upgrade `Django` to `5.2.4`
- Upgrade `django-dsfr` to `3.0.0`
- Upgrade `jsonschema` to `4.25.0`
- Upgrade `sentry-sdk` to `2.33.2`

## [0.2.0] - 2025-06-23

### Changed

#### Dependencies

- Upgrade `Django` to `5.2.3`
- Upgrade `jsonschema` to `4.24.0`
- Upgrade `requests` to `2.32.4`
- Upgrade `urllib3` to `2.5.0`
- Upgrade `pydantic` to `2.10.0`
- Upgrade `pygments` to `2.19.2`

### Added

#### Renewable Management

- add `renewable` app
- add `Renewable` model with admin interface
- add `get_current_quarter_date_range` utility
- add `renewable` dashboard card
- add a formset and view for managing renewable delivery point statuses
- add meter reading management interface with form validation
- add a view for submitted renewable meter readings
- add entity handling with EntityMixin
- add utility functions for quarter-based date operations to handle quarter-specific
  date calculations and conversions
- add factories and seed commands for renewable app
- add test coverage for renewable app
- add `python-dateutil`

#### Notification System

- add user email notifications for renewable submission period opening
- add user email notification for meter reading submissions
- add helper methods for notification management

#### Restricted Period Management

- add restricted period feature for renewable reporting
- add `can_bypass_renewable_period` flag on entities
- add automatic redirection for users outside reporting period
- add a restricted period view

#### Environment variables

- add environment variables for opening period customization
- add environment variables for the time window during which meter readings are accepted
- add environment variables for email notifications

### Deprecated

- add a deprecation warning for ConsentFormView.\_get_entity()

## [0.1.0] - 2025-05-07

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

[unreleased]: https://github.com/MTES-MCT/qualicharge/compare/v0.2.0-dashboard...main
[0.2.0]: https://github.com/MTES-MCT/qualicharge/releases/tag/v0.1.0-dashboard...v0.2.0-dashboard
[0.1.0]: https://github.com/MTES-MCT/qualicharge/releases/tag/v0.1.0-dashboard
