"""Dashboard home app views."""

from django.shortcuts import redirect, render


def user_not_validated_view(request):
    """View to display when the user is not validated."""
    template_name = "auth/user_not_validated.html"

    if request.user.is_validated:
        return redirect("home:index")
    return render(request, template_name, status=403)
