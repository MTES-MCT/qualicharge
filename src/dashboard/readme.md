# QualiCharge Dashboard

The dashboard allows operators to manage all of their data related to qualicharge.

## Access the dashboard

The qualicharge dashboard is available from the url:
[http://localhost:8030](http://localhost:8030).

## Shortcut to use Django manage.py script

```
./bin/manage <your_command>
```

## Useful commands

Bootstrap dashboard project:

```
make bootstrap-dashboard
make run-dashboard
```

Perform a Django migration *(manage.py migrate)*:

```
make migrate-dashboard-db
```

Create superuser:

You can connect with **username: admin** / **password: admin**.
*(The credentials are defined in env.d/dashboard.)*

```
make create-dashboard-superuser
```

Display dashboard logs:

```
make logs-dashboard
```

Reset dashboard db:

```
make drop-dashboard-db
make reset-dashboard-db
```

## Project specific naming convention

For each Django application, the application config label 
(present in my_apps.apps.MyAppConfig) must be of type `qcd_myapp`.

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
There is a signal on the creation of a `delivery point` (`apps.core.models.DeliveryPoint`). 
This signal allows the creation of a `consent` (`apps.consent.models.Consent`) 
corresponding to the `delivery_point`.

## Business logic

### Consent management

3 different status types exist for consents with different management rules:

#### AWAITING

Consent awaiting validation by the user.  
- [x] Users can change consent without restriction.

#### VALIDATED: 

Consent validated by the user.   
It can only be modified under conditions:
-  [x] users cannot modify validated consents,
-  [x] administrators can change a validated consent to `REVOKED`,
-  [x] the updated values are restricted to the `status`, `revoked_date` and 
   `updated_at` 
  fields,
-  [x] validated consent cannot be deleted.

#### REVOKED:

Consent revoked.  
- [ ] It cannot be modified.
- [x] It cannot be deleted.

## API Annuaire des Entreprises

### Documentation

https://entreprise.api.gouv.fr/
https://entreprise.api.gouv.fr/developpeurs

### Information for development

For development, you must use siret `55204944776279`

## License

This work is released under the MIT License (see LICENSE).

