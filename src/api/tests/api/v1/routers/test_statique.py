"""Tests for the QualiCharge API statique router."""

import json

from fastapi import status

from qualicharge.conf import settings
from qualicharge.factories.static import StatiqueFactory
from qualicharge.schemas.utils import save_statique, save_statiques


def test_list(client_auth, db_session):
    """Test the /statique/ list endpoint."""
    # Empty response (no statiques exist)
    response = client_auth.get("/statique/")
    assert response.status_code == status.HTTP_200_OK
    json_response = response.json()
    assert json_response == {
        "limit": 10,
        "offset": 0,
        "previous": None,
        "next": None,
        "items": [],
        "size": 0,
        "total": 0,
    }

    # Create statiques
    n_statiques = 3
    db_statiques = sorted(
        save_statiques(db_session, StatiqueFactory.batch(n_statiques)),
        key=lambda s: s.id_pdc_itinerance,
    )
    response = client_auth.get("/statique/")
    assert response.status_code == status.HTTP_200_OK
    json_response = response.json()
    assert json_response == {
        "limit": 10,
        "offset": 0,
        "previous": None,
        "next": None,
        "items": [json.loads(statique.model_dump_json()) for statique in db_statiques],
        "size": 3,
        "total": 3,
    }


def test_list_pagination(client_auth, db_session):
    """Test the /statique/ list endpoint results pagination."""
    n_statiques = 3
    list(save_statiques(db_session, StatiqueFactory.batch(n_statiques)))

    offset = 0
    limit = 2
    response = client_auth.get(f"/statique/?{offset=}&{limit=}")
    assert response.status_code == status.HTTP_200_OK
    json_response = response.json()
    assert json_response.get("total") == n_statiques
    assert json_response.get("offset") == offset
    assert json_response.get("limit") == limit
    assert json_response.get("size") == limit
    assert json_response.get("previous") is None
    assert json_response.get("next") == "http://testserver/statique/?limit=2&offset=2"

    offset = 2
    response = client_auth.get(f"/statique/?{offset=}&{limit=}")
    assert response.status_code == status.HTTP_200_OK
    json_response = response.json()
    assert json_response.get("total") == n_statiques
    assert json_response.get("offset") == offset
    assert json_response.get("limit") == limit
    assert json_response.get("size") == n_statiques - offset
    assert (
        json_response.get("previous") == "http://testserver/statique/?limit=2&offset=0"
    )
    assert json_response.get("next") is None

    # Edge-case: the last page when limit == size for the last page
    offset = 2
    limit = 1
    response = client_auth.get(f"/statique/?{offset=}&{limit=}")
    assert response.status_code == status.HTTP_200_OK
    json_response = response.json()
    assert json_response.get("total") == n_statiques
    assert json_response.get("offset") == offset
    assert json_response.get("limit") == limit
    assert json_response.get("size") == n_statiques - offset
    assert (
        json_response.get("previous") == "http://testserver/statique/?limit=1&offset=1"
    )
    assert json_response.get("next") is None


def test_read(client_auth, db_session):
    """Test the /statique/{id_pdc_itinerance} endpoint."""
    id_pdc_itinerance = "ESZUNE1111ER1"
    db_statique = save_statique(
        db_session, StatiqueFactory.build(id_pdc_itinerance=id_pdc_itinerance)
    )

    response = client_auth.get(f"/statique/{id_pdc_itinerance}")
    assert response.status_code == status.HTTP_200_OK
    json_response = response.json()
    assert json_response == json.loads(db_statique.model_dump_json())


def test_read_when_statique_does_not_exist(client_auth):
    """Test the /statique/{id_pdc_itinerance} endpoint when item does not exist."""
    id_pdc_itinerance = "ESZUNE1111ER1"
    response = client_auth.get(f"/statique/{id_pdc_itinerance}")
    assert response.status_code == status.HTTP_404_NOT_FOUND
    json_response = response.json()
    assert json_response == {"detail": "Requested statique does not exist"}


def test_create(client_auth):
    """Test the /statique/ create endpoint."""
    id_pdc_itinerance = "ESZUNE1111ER1"
    data = StatiqueFactory.build(
        id_pdc_itinerance=id_pdc_itinerance,
    )

    response = client_auth.post("/statique/", json=json.loads(data.model_dump_json()))
    assert response.status_code == status.HTTP_201_CREATED
    json_response = response.json()
    assert json_response["message"] == "Statique items created"
    assert json_response["size"] == 1
    assert json_response["items"][0]["id_pdc_itinerance"] == id_pdc_itinerance


def test_update(client_auth, db_session):
    """Test the /statique/{id_pdc_itinerance} update endpoint."""
    id_pdc_itinerance = "ESZUNE1111ER1"
    db_statique = save_statique(
        db_session, StatiqueFactory.build(id_pdc_itinerance=id_pdc_itinerance)
    )
    new_statique = db_statique.model_copy(
        update={"contact_oprateur": "john@doe.com"}, deep=True
    )

    response = client_auth.put(
        f"/statique/{id_pdc_itinerance}",
        json=json.loads(db_statique.model_dump_json()),
    )
    assert response.status_code == status.HTTP_200_OK
    json_response = response.json()
    assert json_response == json.loads(new_statique.model_dump_json())


def test_update_on_wrong_id_pdc_itinerance(client_auth):
    """Test the /statique/{id_pdc_itinerance} update endpoint with a mismatching id."""
    id_pdc_itinerance = "ESZUNE1111ER1"
    mismatching_id_pdc_itinerance = "ESZUNE1111ER2"
    statique = StatiqueFactory.build(id_pdc_itinerance=mismatching_id_pdc_itinerance)

    response = client_auth.put(
        f"/statique/{id_pdc_itinerance}",
        json=json.loads(statique.model_dump_json()),
    )
    assert response.status_code == status.HTTP_406_NOT_ACCEPTABLE
    json_response = response.json()
    assert json_response == {"detail": "id_pdc_itinerance does not match request body"}


def test_update_when_statique_does_not_exist(client_auth):
    """Test the /statique/{id_pdc_itinerance} update endpoint with wrong statique."""
    id_pdc_itinerance = "ESZUNE1111ER1"
    statique = StatiqueFactory.build(id_pdc_itinerance=id_pdc_itinerance)

    response = client_auth.put(
        f"/statique/{id_pdc_itinerance}",
        json=json.loads(statique.model_dump_json()),
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND
    json_response = response.json()
    assert json_response == {"detail": "Statique to update does not exist"}


def test_bulk(client_auth):
    """Test the /statique/bulk create endpoint."""
    data = StatiqueFactory.batch(
        size=2,
    )

    payload = [json.loads(d.model_dump_json()) for d in data]
    response = client_auth.post("/statique/bulk", json=payload)

    assert response.status_code == status.HTTP_201_CREATED
    json_response = response.json()
    assert json_response["message"] == "Statique items created"
    assert json_response["size"] == len(payload)
    assert json_response["items"][0]["id_pdc_itinerance"] == data[0].id_pdc_itinerance
    assert json_response["items"][1]["id_pdc_itinerance"] == data[1].id_pdc_itinerance


def test_bulk_with_outbound_sizes(client_auth):
    """Test the /statique/bulk create endpoint with a single or too many entries."""
    id_pdc_itinerance = "ESZUNE1111ER1"

    data = StatiqueFactory.build(
        id_pdc_itinerance=id_pdc_itinerance,
    )
    response = client_auth.post(
        "/statique/bulk", json=[json.loads(data.model_dump_json())]
    )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    data = StatiqueFactory.batch(
        size=settings.API_BULK_CREATE_MAX_SIZE + 1,
    )
    payload = [json.loads(d.model_dump_json()) for d in data]
    response = client_auth.post("/statique/bulk", json=payload)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_bulk_does_not_create_duplicates(client_auth):
    """Test that bulk endpoint does not create duplicates."""
    size = 2
    data = StatiqueFactory.batch(
        size=size,
    )

    payload = [json.loads(d.model_dump_json()) for d in data]
    response = client_auth.post("/statique/bulk", json=payload)
    assert response.status_code == status.HTTP_201_CREATED
    assert len(response.json()["items"]) == size

    payload = [json.loads(d.model_dump_json()) for d in data]
    response = client_auth.post("/statique/bulk", json=payload)
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json() == {"detail": "All Statique entries already exist"}
