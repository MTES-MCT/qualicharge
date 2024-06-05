"""QualiCharge API client models."""

from pydantic import BaseModel


class Token(BaseModel):
    """API Access token."""

    access_token: str
    token_type: str
