"""Dashboard consent app urls."""

from django.urls import path

from .views import ConsentFormView, IndexView

app_name = "consent"

urlpatterns = [
    path("", IndexView.as_view(), name="index"),
    path("manage/", ConsentFormView.as_view(), name="manage"),
    path("manage/<slug:slug>", ConsentFormView.as_view(), name="manage"),
]
