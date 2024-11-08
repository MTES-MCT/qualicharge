"""QualiCharge API load tests."""

import requests
from locust import FastHttpUser, task

API_ADMIN_USER = "admin"
API_ADMIN_PASSWORD = "admin"


class BaseAPIUser(FastHttpUser):
    """Base API user."""

    abstract: bool = True
    username: str
    password: str

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

    def on_start(self):
        """Log user in on start."""
        credentials = {
            "username": self.username,
            "password": self.password,
        }
        response = requests.post(f"{self.host}/auth/token", data=credentials)
        token = response.json()["access_token"]
        self.client.auth_header = f"Bearer {token}"


class APIAdminUser(BaseAPIUser):
    """API admin user."""

    username: str = API_ADMIN_USER
    password: str = API_ADMIN_PASSWORD
