"""Dashboard consent app urls."""

from django.urls import path

from .views import IndexView, ManageView

app_name = "consent"

urlpatterns = [
    path("", IndexView.as_view(), name="index"),
    path("manage/", ManageView.as_view(), name="manage"),
]
