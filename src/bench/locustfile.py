"""QualiCharge API load tests."""

import os
from datetime import datetime, timedelta, timezone
from functools import cache
from pathlib import Path

import pandas as pd
import requests
from locust import FastHttpUser, task

API_ADMIN_USER: str = os.environ["QUALICHARGE_API_ADMIN_USER"]
API_ADMIN_PASSWORD: str = os.environ["QUALICHARGE_API_ADMIN_PASSWORD"]
STATIQUE_DATA_PATH: Path = Path(os.environ["QUALICHARGE_STATIQUE_DATA_PATH"])
STATIC_DB_OFFSET: int = 500


@cache
def load_statique_db(db_path: Path):
    """Load statique database."""
    db = pd.read_json(db_path, dtype_backend="pyarrow", lines=True)
    return db.to_dict(orient="records")


class BaseAPIUser(FastHttpUser):
    """Base API user."""

    abstract: bool = True
    username: str
    password: str
    static_db_path: Path
    counter: dict = {
        "static": {"create": STATIC_DB_OFFSET, "bulk": 10000},
    }

    def on_start(self):
        """Log user in on start."""
        credentials = {
            "username": self.username,
            "password": self.password,
        }
        response = requests.post(f"{self.host}/auth/token", data=credentials)
        token = response.json()["access_token"]
        self.client.auth_header = f"Bearer {token}"
        self.statique_db = load_statique_db(self.static_db_path)

    @task
    def whoami(self):
        """Test the /whoami endpoint."""
        self.client.get("/auth/whoami")

    @task
    def statique_list(self):
        """Assess the /statique GET endpoint."""
        with self.rest("GET", "/statique/?limit=100") as response:
            if response.js["size"] == 0:
                response.failure("Database contains no statique entries")
        with self.rest("GET", "/statique/?limit=10") as response:
            if response.js["size"] == 0:
                response.failure("Database contains no statique entries")

    @task
    def statique_get(self):
        """Assess the /statique/{id_pdc_itinerance} GET endpoint."""
        id_pdc_itinerance = "FRALLEGO002006P3"
        with self.rest("GET", f"/statique/{id_pdc_itinerance}") as response:
            if "id_pdc_itinerance" not in response.js:
                response.failure(
                    f"Database does not contain target statique entry {id_pdc_itinerance}"
                )

    @task
    def statique_update(self):
        """Assess the /statique/{id_pdc_itinerance} PUT endpoint."""
        data = self.statique_db[22]
        data["date_maj"] = "2024-11-21"
        id_pdc_itinerance = data["id_pdc_itinerance"]

        with self.rest("PUT", f"/statique/{id_pdc_itinerance}", json=data) as response:
            if "id_pdc_itinerance" not in response.js:
                response.failure(
                    f"Database does not contain target statique entry {id_pdc_itinerance}"
                )

    @task
    def statique_create(self):
        """Assess the /statique/ POST endpoint."""
        index = self.counter["static"]["create"]
        data = self.statique_db[index]

        with self.rest("POST", "/statique/", json=data) as response:
            if response.status_code == 200 and response.js["size"] == 0:
                response.failure("No Statique entry was created")
            self.counter["static"]["create"] += 1

    @task
    def statique_bulk(self):
        """Assess the /statique/bulk POST endpoint."""
        start = self.counter["static"]["bulk"]
        limit = 50
        end = start + limit
        data = self.statique_db[start:end]

        with self.rest("POST", "/statique/bulk", json=data) as response:
            if response.js["size"] == 0:
                response.failure("No Statique entry was created")
            self.counter["static"]["bulk"] = end

    @task
    def status_list(self):
        """Assess the /dynamique/status/ GET endpoint."""
        with self.rest("GET", "/dynamique/status/") as response:
            if response.status_code == 404:
                response.success()

    @task
    def status_get(self):
        """Assess the /dynamique/status/{id_pdc_itinerance} GET endpoint."""
        id_pdc_itinerance = "FRALLEGO002006P3"
        with self.rest("GET", f"/dynamique/status/{id_pdc_itinerance}") as response:
            if response.status_code == 404:
                response.success()

    @task
    def status_history(self):
        """Assess the /dynamique/status/{id_pdc_itinerance}/history GET endpoint."""
        id_pdc_itinerance = "FRALLEGO002006P3"
        with self.rest(
            "GET", f"/dynamique/status/{id_pdc_itinerance}/history"
        ) as response:
            if response.status_code == 404:
                response.success()

    @task
    def status_create(self):
        """Assess the /dynamique/status/ POST endpoint."""
        now = datetime.now(timezone.utc)
        data = {
            "etat_pdc": "en_service",
            "occupation_pdc": "libre",
            "horodatage": now.isoformat(),
            "etat_prise_type_2": "fonctionnel",
            "etat_prise_type_combo_ccs": "fonctionnel",
            "etat_prise_type_chademo": "fonctionnel",
            "etat_prise_type_ef": "fonctionnel",
            "id_pdc_itinerance": "FRALLEGO002006P3",
        }
        with self.rest("POST", "/dynamique/status/", json=data) as response:
            pass

    @task
    def status_bulk(self):
        """Assess the /dynamique/status/bulk POST endpoint."""
        now = datetime.now(timezone.utc)
        base = {
            "etat_pdc": "en_service",
            "occupation_pdc": "libre",
            "horodatage": now.isoformat(),
            "etat_prise_type_2": "fonctionnel",
            "etat_prise_type_combo_ccs": "fonctionnel",
            "etat_prise_type_chademo": "fonctionnel",
            "etat_prise_type_ef": "fonctionnel",
            "id_pdc_itinerance": "FRALLEGO002006P3",
        }
        delta = timedelta(seconds=3)
        size = 10
        data = [
            dict(base, horodatage=(now - delta * n).isoformat()) for n in range(size)
        ]

        with self.rest("POST", "/dynamique/status/bulk", json=data) as response:
            pass

    @task
    def session_create(self):
        """Assess the /dynamique/session/ POST endpoint."""
        now = datetime.now(timezone.utc)
        data = {
            "start": (now - timedelta(hours=1)).isoformat(),
            "end": (now - timedelta(minutes=1)).isoformat(),
            "energy": 666.66,
            "id_pdc_itinerance": "FRALLEGO002006P3",
        }
        with self.rest("POST", "/dynamique/session/", json=data) as response:
            pass

    @task
    def session_bulk(self):
        """Assess the /dynamique/session/bulk POST endpoint."""
        now = datetime.now(timezone.utc)
        base = {
            "start": (now - timedelta(hours=1)).isoformat(),
            "end": (now - timedelta(minutes=1)).isoformat(),
            "energy": 666.66,
            "id_pdc_itinerance": "FRALLEGO002006P3",
        }
        delta = timedelta(seconds=3)
        size = 10
        data = [
            dict(
                base,
                start=(now - timedelta(hours=n, minutes=30)).isoformat(),
                end=(now - timedelta(hours=n)).isoformat(),
                energy=666.66 * (n + 1),
            )
            for n in range(size)
        ]

        with self.rest("POST", "/dynamique/session/bulk", json=data) as response:
            pass


class APIAdminUser(BaseAPIUser):
    """API admin user."""

    username: str = API_ADMIN_USER
    password: str = API_ADMIN_PASSWORD
    static_db_path: Path = STATIQUE_DATA_PATH
