"""Dashboard auth models."""

from django.contrib.auth.models import AbstractUser


class DashboardUser(AbstractUser):
    """Represents a user in the Dashboard application, extending the AbstractUser model.

    Designed to be used as part of the system's authentication and user
    management functionality, incorporating the fields and methods provided by the
    AbstractUser model in Django.
    """

    pass
