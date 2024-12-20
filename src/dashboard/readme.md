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

## License

This work is released under the MIT License (see LICENSE).
