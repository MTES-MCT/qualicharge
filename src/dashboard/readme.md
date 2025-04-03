# QualiCharge Dashboard

The dashboard allows operators to manage all of their data related to qualicharge.

## Access the dashboard

The qualicharge dashboard is available from the url:
[http://localhost:8030](http://localhost:8030).

## Shortcut to use Django `manage.py` script

```
./bin/manage <your_command>
```

## Useful commands

### Bootstrap Dashboard Project

```
make bootstrap-dashboard
make run-dashboard
```

### Bootstrap the QualiCharge API 

(this is required to integrate the QualiCharge API with the dashboard):

```
make bootstrap-api
make run-api
```

### Perform a Django migration *(manage.py migrate)*

```
make migrate-dashboard-db
```

### Create Superuser

You can connect with **username: admin** / **password: admin**.
*(The credentials are defined in env.d/dashboard.)*

```
make create-dashboard-superuser
```

### Display Dashboard logs

```
make logs-dashboard
```

### Reset the Dashboard db

```
make drop-dashboard-db
make reset-dashboard-db
```

## Project specific naming convention

For each Django application, the application config label 
(present in my_apps.apps.MyAppConfig) must have the format `qcd_myapp`.

i.e. for the `home` app:  
```python
class HomeConfig(AppConfig):
    """Home app config."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.home"
    label = "qcd_home"  # prefix app name with 'qcd_'
```

## Signals

### apps.consent.signals.handle_new_delivery_point()

A signal is triggered when a `delivery_point` (`apps.core.models.DeliveryPoint`) is created.  
This signal allows the creation of a `consent` (`apps.consent.models.Consent`)  
corresponding to the `delivery_point`.

## Business logic

### WorkFlow

```mermaid
---
config:
  theme: neutral
  look: classic
  layout: dagre
---
flowchart LR
    Start(["Start"]) --> A1["User Login with ProConnect"]
    A1 --> B1["Is it the first login?"]
    B1 -- Yes --> C1["Create user and save SIRET from ProConnect"]
    C1 --> C3["Create an entity with the user's SIRET via 'Annuaire des Entreprises' API"] & C2["Send an admin notification"]
    B1 -- No --> D1["Is the user validated?"]
    D1 -- Yes --> D2["User access to the dashboard"]
    D1 -- No --> D3["Redirect user to a restricted view due to insufficient permissions"] & D4["Admin validates user in the admin panel"]
    D4 --> D5["Send notification to the user: 'Your account is activated'"]
    D2 --> E0(["Consents Management"]) 
    E0 --> E1(["User Consents Validation"]) & F1(["User views validated consents"])
    E1 --> E2["User fills fields and verifies information in the consent form"]
    E2 --> E3["Send notification: 'Your consents are validated successfully.'"]
    F1 --> F2["User views validated consents for the active period"]
```

### Consent management

There are three different status types for consents, each with specific management rules:

#### AWAITING

Consent awaiting validation by the user.  
- [x] Users can change consents without restriction.

#### VALIDATED

Consent validated by the user.   
It can only be modified under conditions:
-  [x] users cannot modify validated consents,
-  [x] administrators can change a validated consent to `REVOKED`,
-  [x] modifiable fields are restricted to `status`, `revoked_date`, and `updated_at`,
-  [x] validated consents cannot be deleted.

#### REVOKED

Consent revoked.  
- [x] It cannot be modified.
- [x] It cannot be deleted.

## Emails

The third-party service **BREVO** is used to send emails.

### List of Emails Sent

| **Description**     | **Target**       | **BREVO Template ID** |
|----------------------|------------------|------------------------|
| New user creation    | Admins           | 4                      |
| Admin validation     | Users            | 5                      |
| Consents awaiting    | Users            | 6                      |
| Consents validated   | Users            | 3                      |

## Django Commands

### Commands used with Cron Job

- `syncdeliverypoints`: Synchronize delivery points from the QualiCharge API 
- `renewconsents`: Renew consents (duplicate expiring consents and generate new consents)
- `notifawaitingconsents`: Notify users of their pending consents

### Commands used in development only

- `populateentity`: Retrieve company information using its SIRET via the "Annuaire des Entreprises" API
- `seed_consent`: Seed sample consents

## Third Party Services

### ProConnect

#### Documentation

https://github.com/numerique-gouv/proconnect-documentation/blob/main/doc_fs/README.md

#### Development Information 

To test the connection to ProConnect, you can use:   
- **login:** user@yopmail.com  
- **password:** user@yopmail.com

### API Annuaire des Entreprises API

#### Documentation

https://entreprise.api.gouv.fr/  
https://entreprise.api.gouv.fr/developpeurs

#### Development Information 

For development, use the following SIRET `55204944776279`

## License

This work is released under the MIT License (see LICENSE).
