"""Dashboard auth admin."""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import DashboardUser


@admin.register(DashboardUser)
class DashboardUserAdmin(UserAdmin):
    """Dashboard user admin based on UserAdmin."""

    pass
