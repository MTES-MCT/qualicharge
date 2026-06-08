"""QualiCharge models utilities."""

from typing import Generic, List, Type, TypeVar

from pydantic import AnyHttpUrl, BaseModel, computed_field
from sqlmodel import SQLModel

T = TypeVar("T")


class ModelSchemaMixin:
    """A mixin that adds Pydantic to SQLModel helpers."""

    def get_fields_for_schema(self, schema: Type[SQLModel]):
        """Get input schema-related fields/values as a dict."""
        return self.model_dump(include=set(schema.model_fields.keys()))  # type: ignore[attr-defined]


class PaginatedListResponse(BaseModel, Generic[T]):
    """Paginated list response."""

    limit: int
    offset: int
    total: int
    previous: AnyHttpUrl | None
    next: AnyHttpUrl | None
    items: List[T]

    @computed_field  # type: ignore[misc]
    @property
    def size(self) -> int:
        """The number of items returned."""
        return len(self.items)
