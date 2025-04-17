"""Dashboard renewable meter app urls."""

from django.urls import path

from .views import IndexView

app_name = "renewable"

urlpatterns = [
    path("", IndexView.as_view(), name="index"),
]
