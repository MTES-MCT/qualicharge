"""Authentication model factories."""

import uuid
from datetime import datetime
from typing import Any, Dict

from polyfactory import PostGenerated
from polyfactory.factories.pydantic_factory import ModelFactory
from polyfactory.pytest_plugin import register_fixture

from qualicharge.conf import settings

from .models import IDToken


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
