"""Dashboard consent app urls."""

from django.urls import path
from django.views.generic.base import RedirectView

from .views import ConsentFormView, IndexView, ValidatedConsentView

app_name = "consent"

urlpatterns = [
    path("", IndexView.as_view(), name="index"),
    # editing multiple entities at once is no longer available,
    # instead we redirect to the `index` page.
    path(
        "manage/",
        RedirectView.as_view(pattern_name="consent:index", permanent=False),
        name="manage",
    ),
    path("manage/<slug:slug>", ConsentFormView.as_view(), name="manage"),
    path(
        "validated/",
        RedirectView.as_view(pattern_name="consent:index", permanent=False),
        name="validated",
    ),
    path("validated/<slug:slug>", ValidatedConsentView.as_view(), name="validated"),
]
