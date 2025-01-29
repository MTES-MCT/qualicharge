"""Dashboard auth middleware."""

from django.contrib.auth.middleware import LoginRequiredMiddleware  # type: ignore
from django.urls import reverse


class DashboardLoginRequiredMiddleware(LoginRequiredMiddleware):
    """Middleware that redirects all unauthenticated requests to a login page.

    Override the original LoginRequiredMiddleware to allow OIDC views to be accessed.
    Thanks to Agnès Haasser for the tip.
    """

    def process_view(self, request, view_func, view_args, view_kwargs):
        """Override the original process_view method.

        Allow OIDC views to be accessed.
        """
        if request.user.is_authenticated:
            return None

        if not getattr(view_func, "login_required", True):
            return None

        # allow OIDC views
        if request.path in (
            reverse("oidc_authentication_init"),
            reverse("oidc_authentication_callback"),
        ):
            return None

        return self.handle_no_permission(request, view_func)
