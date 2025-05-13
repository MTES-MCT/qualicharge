"""Dashboard renewable meter app urls."""

from django.urls import path
from django.views.generic.base import RedirectView

from .views import (
    IndexView,
    RenewableMetterReadingFormView,
    SubmittedRenewableView,
)

app_name = "renewable"

urlpatterns = [
    path("", IndexView.as_view(), name="index"),
    path("manage/<slug:slug>", RenewableMetterReadingFormView.as_view(), name="manage"),
    # direct access to `manage/` is not allowed
    path(
        "manage/",
        RedirectView.as_view(pattern_name="renewable:index", permanent=False),
        name="manage",
    ),
    path("submitted/<slug:slug>", SubmittedRenewableView.as_view(), name="submitted"),
]
