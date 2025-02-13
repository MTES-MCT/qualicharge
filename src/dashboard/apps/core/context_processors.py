"""Dashboard core context processors."""

from django.conf import settings


def contact_email(request):
    """Context processor to add CONTACT_EMAIL to the context."""
    return {"contact_email": settings.CONTACT_EMAIL}
