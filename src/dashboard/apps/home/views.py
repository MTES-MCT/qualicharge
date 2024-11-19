"""Dashboard home app views."""

from django.views.generic import TemplateView


class IndexView(TemplateView):
    """Index view of the homepage."""

    template_name = "home/index.html"
