"""Dashboard core app views."""

from apps.auth.mixins import UserValidationMixin
from apps.consent.mixins import BreadcrumbContextMixin


class BaseView(UserValidationMixin, BreadcrumbContextMixin):
    """Base view."""

    pass
