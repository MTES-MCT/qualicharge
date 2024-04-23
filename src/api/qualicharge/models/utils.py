"""QualiCharge models utilities."""

from typing import Type

from sqlmodel import SQLModel


class ModelSchemaMixin:
    """A mixin that adds Pydantic to SQLModel helpers."""

    def get_fields_for_schema(self, schema: Type[SQLModel]):
        """Get input schema-related fields/values as a dict."""
        return self.model_dump(include=set(schema.model_fields.keys()))  # type: ignore[attr-defined]
