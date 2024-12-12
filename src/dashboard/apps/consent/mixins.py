"""Dashboard consent app mixins."""

from django.views.generic.base import ContextMixin
from django_stubs_ext import StrOrPromise


class BreadcrumbContextMixin(ContextMixin):
    """Mixin to simplify usage of the `dsfr_breadcrumb` in class based views.

    Add the breadcrumb elements in the view context for the dsfr breadcrumb:
    https://numerique-gouv.github.io/django-dsfr/components/breadcrumb/.

    ```python
        breadcrumb_links = [{"url": "first-url", "title": "First title"}, {...}],
        breadcrumb_current: "Current page title",
        breadcrumb_root_dir: "the root directory, if the site is not installed at the
        root of the domain"
    }
    ```
    """

    breadcrumb_links: list[dict[StrOrPromise, StrOrPromise]] | None = None
    breadcrumb_current: StrOrPromise | None = None
    breadcrumb_root_dir: StrOrPromise | None = None

    def get_context_data(self, **kwargs) -> dict:
        """Add breadcrumb context to the view."""
        context = super().get_context_data(**kwargs)

        context["breadcrumb_data"] = {
            "links": self.breadcrumb_links,
            "current": self.breadcrumb_current,
        }
        if self.breadcrumb_root_dir:
            context["breadcrumb_data"]["root_dir"] = self.breadcrumb_root_dir

        return context
