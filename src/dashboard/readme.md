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

Perform a Django migration *(manage.py migrate)* :

```
make migrate-dashboard-db
```

Create superuser.

You can connect with **username: admin** / **password: admin**.
*(The credentials are defined in env.d/dashboard.)*

```
make create-dashboard-superuser
```

Display dashboard logs

```
make logs-dashboard
```

## License

This work is released under the MIT License (see LICENSE).
