"""Dashboard home app urls."""

from django.urls import path

from .views import IndexView

app_name = "home"

urlpatterns = [
    path("", IndexView.as_view(), name="index"),
]
