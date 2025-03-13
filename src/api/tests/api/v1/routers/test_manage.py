"""Tests for the QualiCharge API dynamic router."""

import pytest
from fastapi import status
from sqlmodel import select

from qualicharge.api.v1.routers.manage import DashboardStation
from qualicharge.auth.schemas import ScopesEnum
from qualicharge.factories.static import (
    StatiqueFactory,
)
from qualicharge.schemas.core import (
    PointDeCharge,
    Station,
)
from qualicharge.schemas.utils import save_statiques


@pytest.mark.parametrize(
    "client_auth",
    (
        (True, {"is_superuser": False, "scopes": []}),
        *[
            (True, {"is_superuser": False, "scopes": [scope]})
            for scope in ScopesEnum
            if scope != ScopesEnum.MANAGE_READ
        ],
    ),
    indirect=True,
)
def test_stations_by_siren_with_missing_scopes(client_auth):
    """Test the /status/ get endpoint scopes."""
    response = client_auth.get("/manage/station/siren/123456789")
    assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.parametrize(
    "client_auth",
    (
        (True, {"is_superuser": True, "scopes": []}),
        (True, {"is_superuser": False, "scopes": [ScopesEnum.MANAGE_READ]}),
    ),
    indirect=True,
)
def test_stations_by_siren_for_user(db_session, client_auth):
    """Test the /status/ get endpoint (superuser case)."""
    # Station not found
    response = client_auth.get("/manage/station/siren/123456789")
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json() == {"detail": "No station corresponds to your request"}

    # Create statique entries using two amenageurs and related stations
    batches = ((3, "123456789"), (2, "012345678"))
    for batch in batches:
        save_statiques(
            db_session,
            [
                StatiqueFactory.build(
                    siren_amenageur=batch[1],
                    num_pdl=StatiqueFactory.__faker__.pystr_format("##############"),
                )
                for _ in range(batch[0])
            ],
        )
    pdcs = db_session.exec(select(PointDeCharge)).all()
    assert len(pdcs) == sum([b[0] for b in batches])

    # Get stations by SIREN
    for batch in batches:
        response = client_auth.get(f"/manage/station/siren/{batch[1]}")
        assert response.status_code == status.HTTP_200_OK
        stations = [DashboardStation(**s) for s in response.json()]
        assert len(stations) == batch[0]

        for station in stations:
            db_station = db_session.exec(
                select(Station).where(
                    Station.id_station_itinerance == station.id_station_itinerance
                )
            ).one()
            assert station.id_station_itinerance == db_station.id_station_itinerance
            assert station.nom_station == db_station.nom_station
            assert station.num_pdl == db_station.num_pdl
            assert station.updated_at == db_station.updated_at
