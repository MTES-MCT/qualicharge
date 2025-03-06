"""Dashboard consent app urls."""

from django.urls import path

from apps.auth.views import user_not_validated_view

app_name = "qcd_auth"

urlpatterns = [
    path("pending/", user_not_validated_view, name="not_validated"),
]
