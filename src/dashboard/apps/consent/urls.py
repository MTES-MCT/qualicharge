"""Dashboard consent app urls."""

from django.urls import path

from .views import IndexView, consent_form_view

app_name = "consent"

urlpatterns = [
    path("", IndexView.as_view(), name="index"),
    path("manage/", consent_form_view, name="manage"),
    path("manage/<slug:slug>", consent_form_view, name="manage"),
]
