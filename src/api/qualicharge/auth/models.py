"""Authentication models."""

from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr


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


class User(BaseModel):
    """QualiCharge user."""

    email: EmailStr
