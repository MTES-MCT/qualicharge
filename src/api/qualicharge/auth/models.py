"""Authentication models."""

from typing import List, Optional

from pydantic import BaseModel, ConfigDict, EmailStr

from .schemas import ScopesEnum


class IDToken(BaseModel):
    """Pydantic model representing the core of an OpenID Connect ID Token.

    ID Tokens are polymorphic and may have many attributes not defined in the
    specification. This model ignores all additional fields.

    Attributes:
        iss (str): Issuer Identifier for the Issuer of the response.
        sub (str): Subject Identifier.
        aud (str): Audience(s) that this ID Token is intended for.
        exp (int): Expiration time on or after which the ID Token MUST NOT be
                   accepted for processing.
        iat (int): Time at which the JWT was issued.
        scope (str): Scope(s) for resource authorization.
    """

    iss: str
    sub: str
    aud: Optional[str]
    exp: int
    iat: int
    scope: Optional[str]
    email: EmailStr

    model_config = ConfigDict(extra="ignore")


class UserRead(BaseModel):
    """QualiCharge user read model."""

    username: str
    email: EmailStr
    first_name: Optional[str]
    last_name: Optional[str]
    is_active: bool
    is_staff: bool
    is_superuser: bool

    # Permissions
    scopes: List[ScopesEnum] = []

    # Relationships
    groups: List[str] = []
