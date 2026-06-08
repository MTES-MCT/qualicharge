"""Shared IRVE identifier types."""

from pydantic import Field, StringConstraints
from typing_extensions import Annotated

IdStationItinerance = Annotated[
    str,
    StringConstraints(
        pattern="(^FR[A-Z0-9]{3}P[A-Z0-9]{1,29}$|Non concerné)",
        strip_whitespace=True,
    ),
]

IdPdcItinerance = Annotated[
    str,
    StringConstraints(
        pattern="(^FR[A-Z0-9]{3}E[A-Z0-9]{1,29}$|Non concerné)",
        strip_whitespace=True,
    ),
    Field(
        examples=["FR0NXEVSEXB9YG", "FRFASE3300405", "FR073E012308585"],
    ),
]
