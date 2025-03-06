"""Dashboard auth mixins."""

from django.shortcuts import redirect


class UserValidationMixin:
    """Mixin to check if the request.user is validated."""

    not_validated_template_name = "auth/user_not_validated.html"

    def dispatch(self, request, *args, **kwargs):
        """Check if the user is validated."""
        if not getattr(request.user, "is_validated", False):
            return redirect("qcd_auth:not_validated")
        return super().dispatch(request, *args, **kwargs)
