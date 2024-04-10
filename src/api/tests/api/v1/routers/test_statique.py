"""Tests for the QualiCharge API statique router."""

import json

from fastapi import status

from qualicharge.conf import settings
from qualicharge.factories.static import StatiqueFactory


def test_list(client_auth):
    """Test the /statique/ list endpoint."""
    response = client_auth.get("/statique/")
    assert response.status_code == status.HTTP_200_OK
    json_response = response.json()
    expected_size = 0
    assert len(json_response) == expected_size


def test_create(client_auth):
    """Test the /statique/ create endpoint."""
    telephone_operateur = "0123456789"
    id_station_itinerance = "ESZUNP8891687432127666088"
    id_pdc_itinerance = "ESZUNE1111ER1"
    data = StatiqueFactory.build(
        telephone_operateur=telephone_operateur,
        id_station_itinerance=id_station_itinerance,
        id_pdc_itinerance=id_pdc_itinerance,
    )

    response = client_auth.post("/statique/", json=json.loads(data.model_dump_json()))
    assert response.status_code == status.HTTP_201_CREATED
    json_response = response.json()
    assert json_response["message"] == "Statique items created"
    assert json_response["size"] == 1
    assert json_response["items"][0]["id_pdc_itinerance"] == id_pdc_itinerance


def test_bulk(client_auth):
    """Test the /statique/bulk create endpoint."""
    telephone_operateur = "0123456789"
    id_station_itinerance = "ESZUNP8891687432127666088"
    id_pdc_itinerance = "ESZUNE1111ER1"
    data = StatiqueFactory.batch(
        size=2,
        telephone_operateur=telephone_operateur,
        id_station_itinerance=id_station_itinerance,
        id_pdc_itinerance=id_pdc_itinerance,
    )

    payload = [json.loads(d.model_dump_json()) for d in data]
    response = client_auth.post("/statique/bulk", json=payload)

    assert response.status_code == status.HTTP_201_CREATED
    json_response = response.json()
    assert json_response["message"] == "Statique items created"
    assert json_response["size"] == len(payload)
    assert json_response["items"][0]["id_pdc_itinerance"] == id_pdc_itinerance
    assert json_response["items"][1]["id_pdc_itinerance"] == id_pdc_itinerance


def test_bulk_with_outbound_sizes(client_auth):
    """Test the /statique/bulk create endpoint with a single or too many entries."""
    telephone_operateur = "0123456789"
    id_station_itinerance = "ESZUNP8891687432127666088"
    id_pdc_itinerance = "ESZUNE1111ER1"

    data = StatiqueFactory.build(
        telephone_operateur=telephone_operateur,
        id_station_itinerance=id_station_itinerance,
        id_pdc_itinerance=id_pdc_itinerance,
    )
    response = client_auth.post(
        "/statique/bulk", json=[json.loads(data.model_dump_json())]
    )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    data = StatiqueFactory.batch(
        size=settings.API_BULK_CREATE_MAX_SIZE + 1,
        telephone_operateur=telephone_operateur,
        id_station_itinerance=id_station_itinerance,
        id_pdc_itinerance=id_pdc_itinerance,
    )
    payload = [json.loads(d.model_dump_json()) for d in data]
    response = client_auth.post("/statique/bulk", json=payload)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
