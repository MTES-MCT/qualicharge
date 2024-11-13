"""Dashboard home app views."""

from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView


class IndexView(LoginRequiredMixin, TemplateView):
    """Index view of the homepage."""

    template_name = "home/index.html"
