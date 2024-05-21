"""Authentication model factories."""

import uuid
from datetime import datetime
from typing import Any, Dict

from polyfactory import PostGenerated, Use
from polyfactory.factories.pydantic_factory import ModelFactory
from polyfactory.pytest_plugin import register_fixture

from qualicharge.conf import settings
from qualicharge.factories import FrenchDataclassFactory, TimestampedSQLModelFactory

from .models import IDToken
from .schemas import Group, ScopesEnum, User


def set_token_exp(name: str, values: Dict[str, int], *args: Any, **kwargs: Any) -> int:
    """Set token expiracy field base on the iat."""
    return values["iat"] + 300


@register_fixture(name="id_token_factory")
class IDTokenFactory(ModelFactory[IDToken]):
    """IDToken model factory."""

    iss = "http://keycloak:8080/realms/qualicharge"
    sub = str(uuid.uuid4())
    aud = settings.OIDC_EXPECTED_AUDIENCE
    exp = PostGenerated(set_token_exp)
    iat = int(datetime.now().timestamp())
    scope = "email profile"
    email = "john@doe.com"


class UserFactory(TimestampedSQLModelFactory[User]):
    """User schema factory."""

    username = Use(
        lambda: FrenchDataclassFactory.__faker__.simple_profile().get("username")
    )
    email = Use(FrenchDataclassFactory.__faker__.ascii_company_email)
    first_name = Use(FrenchDataclassFactory.__faker__.first_name)
    last_name = Use(FrenchDataclassFactory.__faker__.last_name)
    scopes = Use(FrenchDataclassFactory.__random__.sample, list(ScopesEnum), 2)


class GroupFactory(TimestampedSQLModelFactory[Group]):
    """Group schema factory."""

    name = Use(FrenchDataclassFactory.__faker__.company)
