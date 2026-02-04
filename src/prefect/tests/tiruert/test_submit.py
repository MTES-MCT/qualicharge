"""QualiCharge prefect tiruert tests: Submit."""

from datetime import date, datetime
from zoneinfo import ZoneInfo

from sqlalchemy import text

from indicators.types import Environment
from tiruert import submit as tiruert_submit
from tiruert.run import tiruert_for_day_and_amenageur


def test_task_get_amenageurs_siren():
    """Test the `get_amenageurs_siren` task."""
    sirens = tiruert_submit.get_amenageurs_siren(Environment.TEST)
    expected = 25
    assert len(sirens) == expected


def test_task_extract(indicators_db_engine):
    """Test the `extract` task."""
    # Store energies for the 2024/12/27 day
    tiruert_for_day_and_amenageur(Environment.TEST, date(2024, 12, 27), "891118473")

    # We query only energies stored for the 2024/12/27 day
    df = tiruert_submit.extract(
        Environment.TEST, date(2024, 12, 25), date(2024, 12, 27), "891118473"
    )
    assert set(df.columns) == {
        "entity",
        "siren",
        "code",
        "station",
        "energy_mwh",
    }
    n_stations = 268
    assert len(df) == n_stations
    assert len(df[df.station == "FRPD1PACCSAT"].energy_mwh.values) == 1
    energy = 0.047208
    assert df[df.station == "FRPD1PACCSAT"].energy_mwh.values[0] == energy

    # Store energies for the 2024/12/28 day
    tiruert_for_day_and_amenageur(Environment.TEST, date(2024, 12, 28), "891118473")

    # We query (again) only energy stored for the 2024/12/27 day to ensure nothing has
    # altered expected results
    df = tiruert_submit.extract(
        Environment.TEST, date(2024, 12, 25), date(2024, 12, 27), "891118473"
    )
    n_stations = 268
    assert len(df) == n_stations
    assert len(df[df.station == "FRPD1PACCSAT"].energy_mwh.values) == 1
    energy = 0.047208
    assert df[df.station == "FRPD1PACCSAT"].energy_mwh.values[0] == energy

    # We now query energy stored for the 2024/12/28 day
    df = tiruert_submit.extract(
        Environment.TEST, date(2024, 12, 28), date(2024, 12, 28), "891118473"
    )
    n_stations = 263
    assert len(df) == n_stations
    assert len(df[df.station == "FRPD1PACCSAT"].energy_mwh.values) == 1
    energy = 0.096214
    assert df[df.station == "FRPD1PACCSAT"].energy_mwh.values[0] == energy

    # Now we extend the period for a two-days trail. Energy should be the sum.
    df = tiruert_submit.extract(
        Environment.TEST, date(2024, 12, 25), date(2024, 12, 29), "891118473"
    )
    n_stations = 358
    assert len(df) == n_stations
    assert len(df[df.station == "FRPD1PACCSAT"].energy_mwh.values) == 1
    energy = 0.143422
    assert df[df.station == "FRPD1PACCSAT"].energy_mwh.values[0] == energy


def test_task_transform(indicators_db_engine):
    """Test the `transform` task."""
    # Prepare data
    tiruert_for_day_and_amenageur(Environment.TEST, date(2024, 12, 27), "891118473")
    tiruert_for_day_and_amenageur(Environment.TEST, date(2024, 12, 28), "891118473")
    energy_by_station = tiruert_submit.extract(
        Environment.TEST, date(2024, 12, 27), date(2024, 12, 28), "891118473"
    )

    # Generate the payload
    payload = tiruert_submit.transform(
        date(2024, 12, 27),
        date(2024, 12, 28),
        "891118473",
        energy_by_station,
    )
    assert len(payload) == 1
    amenageur = payload[0]
    assert amenageur["entity"] == "Power Dot France"
    assert amenageur["siren"] == "891118473"
    assert len(amenageur["operational_units"]) == 1
    ou = amenageur["operational_units"][0]
    assert ou["code"] == "FRPD1"
    assert ou["from"] == "2024-12-27"
    assert ou["to"] == "2024-12-28"
    n_stations = 358
    assert len(ou["stations"]) == n_stations
    assert [s for s in ou["stations"] if s["id"] == "FRPD1PACCSAT"] == [
        {"id": "FRPD1PACCSAT", "energy": 0.143422, "is_controlled": False}
    ]


def test_task_load(indicators_db_engine):
    """Test the `load` task."""
    # Prepare data
    payload = [
        {
            "entity": "Power Dot France",
            "siren": "891118473",
            "operational_units": [
                {
                    "code": "FRPD1",
                    "from": "2024-12-27",
                    "to": "2024-12-28",
                    "stations": [
                        {
                            "id": "FRPD1PACCSAT",
                            "energy": 1.434220e-04,
                            "is_controlled": False,
                        },
                        {
                            "id": "FRPD1PACCVIL",
                            "energy": 0.000073,
                            "is_controlled": False,
                        },
                    ],
                },
            ],
        }
    ]
    tiruert_submit.load(
        Environment.TEST,
        "891118473",
        0.000216422,
        date(2024, 12, 1),
        payload,
    )
    with indicators_db_engine.connect() as connection:
        result = connection.execute(
            text(
                "SELECT * FROM test "
                "WHERE code = 'tirue' "
                "AND level = 6 "
                "AND target = '891118473' "
                "AND period = 'm' "
            )
        )
    # We should have saved only a single for for FRPD1 over this period
    records = result.all()
    assert len(records) == 1
    total = 0.000216422
    assert records[0].target == "891118473"
    assert records[0].value == total
    assert records[0].code == "tirue"
    expected_level = 6
    assert records[0].level == expected_level
    assert records[0].period == "m"
    assert records[0].timestamp == datetime(
        2024, 12, 1, 0, 0, tzinfo=ZoneInfo(key="Etc/UTC")
    )
    assert records[0].category is None
    assert records[0].extras == payload


def test_task_submit(responses):
    """Test the `submit` task."""
    payload = [
        {
            "entity": "Power Dot France",
            "siren": "891118473",
            "operational_units": [
                {
                    "code": "FRPD1",
                    "from": "2024-12-27",
                    "to": "2024-12-28",
                    "stations": [
                        {
                            "id": "FRPD1PACCSAT",
                            "energy": 1.434220e-04,
                            "is_controlled": False,
                        },
                        {
                            "id": "FRPD1PACCVIL",
                            "energy": 0.000073,
                            "is_controlled": False,
                        },
                    ],
                },
            ],
        }
    ]

    # Success
    responses.post(
        "http://localhost:8088/api/elec/provision-certificates-qualicharge/bulk-create/",
        status=201,
    )
    result = tiruert_submit.submit(payload, "891118473", date(2024, 12, 1))
    assert (
        result.message
        == "Monthly volumes sent for amenageur 891118473 (date: 2024-12-01)"
    )

    # Failed
    responses.post(
        "http://localhost:8088/api/elec/provision-certificates-qualicharge/bulk-create/",
        status=400,
        json={
            "status": "failed",
            "errors": ["Invalid data"],
        },
    )
    result = tiruert_submit.submit(payload, "891118473", date(2024, 12, 1))
    assert (
        result.message
        == "CARBURE submission failed for amenageur 891118473 (date: 2024-12-01)"
    )


def test_flow_tiruert_for_month_and_amenageur(indicators_db_engine, responses):
    """Test the `tiruert_for_month_and_amenageur` flow."""
    # Add test data
    tiruert_for_day_and_amenageur(Environment.TEST, date(2024, 12, 27), "891118473")
    tiruert_for_day_and_amenageur(Environment.TEST, date(2024, 12, 28), "891118473")

    # Mock successful submission
    responses.post(
        "http://localhost:8088/api/elec/provision-certificates-qualicharge/bulk-create/",
        status=201,
    )
    tiruert_submit.tiruert_for_month_and_amenageur(
        Environment.TEST, year=2024, month=12, siren="891118473"
    )
    with indicators_db_engine.connect() as connection:
        result = connection.execute(
            text(
                "SELECT * FROM test "
                "WHERE code = 'tirue' "
                "AND level = 6 "
                "AND target = '891118473' "
                "AND period = 'm' "
            )
        )
    # We should have saved only a single for for FRPD1 over this period
    records = result.all()
    assert len(records) == 1
    assert records[0].target == "891118473"


def test_flow_tiruert_for_month_and_amenageur_failed_submission(
    indicators_db_engine, responses
):
    """Test the `tiruert_for_month_and_amenageur` flow when submission fails."""
    # Add test data
    tiruert_for_day_and_amenageur(Environment.TEST, date(2024, 12, 27), "891118473")
    tiruert_for_day_and_amenageur(Environment.TEST, date(2024, 12, 28), "891118473")

    # Mock failed submission
    responses.post(
        "http://localhost:8088/api/elec/provision-certificates-qualicharge/bulk-create/",
        status=400,
        json={
            "status": "validation_error",
            "errors": ["Misc"],
        },
    )
    # It is supposed to fail without raising an exception
    tiruert_submit.tiruert_for_month_and_amenageur(
        Environment.TEST, year=2024, month=12, siren="891118473"
    )

    with indicators_db_engine.connect() as connection:
        result = connection.execute(
            text(
                "SELECT COUNT(*) FROM test "
                "WHERE code = 'tirue' "
                "AND level = 6 "
                "AND target = '891118473' "
                "AND period = 'm' "
            )
        )
    # Nothing should have been saved if the submission to CARBURE failed
    assert result.one()[0] == 0


def test_flow_tiruert_for_month_failed_submission(
    indicators_db_engine, responses, monkeypatch
):
    """Test the `tiruert_for_month` flow."""
    # Add test data
    tiruert_for_day_and_amenageur(
        Environment.TEST, date(2024, 12, 27), "891118473"
    )  # FRPD1
    tiruert_for_day_and_amenageur(
        Environment.TEST, date(2024, 12, 28), "891118473"
    )  # FRPD1
    tiruert_for_day_and_amenageur(
        Environment.TEST, date(2024, 12, 25), "524335262"
    )  # FRTSL

    # Mock failed submission for FRPD1
    responses.post(
        "http://localhost:8088/api/elec/provision-certificates-qualicharge/bulk-create/",
        status=400,
        json={
            "status": "validation_error",
            "errors": ["Misc"],
        },
    )
    # # Mock successful submission for FRTSL
    responses.post(
        "http://localhost:8088/api/elec/provision-certificates-qualicharge/bulk-create/",
        status=201,
    )

    # Pretend to have only two amenageurs to speed up test execution
    monkeypatch.setattr(
        tiruert_submit, "get_amenageurs_siren", lambda _: ["891118473", "524335262"]
    )

    tiruert_submit.tiruert_for_month(Environment.TEST, year=2024, month=12)
    with indicators_db_engine.connect() as connection:
        result = connection.execute(
            text(
                "SELECT * FROM test "
                "WHERE code = 'tirue' "
                "AND level = 6 "
                "AND period = 'm' "
            )
        )
    # We should have saved only a single for for FRPD1 over this period
    records = result.mappings().all()
    expected = 1
    assert len(records) == expected
    assert records[0]["target"] == "524335262"


def test_flow_tiruert_for_month(indicators_db_engine, responses, monkeypatch):
    """Test the `tiruert_for_month` flow."""
    # Add test data
    tiruert_for_day_and_amenageur(
        Environment.TEST, date(2024, 12, 27), "891118473"
    )  # FRPD1
    tiruert_for_day_and_amenageur(
        Environment.TEST, date(2024, 12, 28), "891118473"
    )  # FRPD1
    tiruert_for_day_and_amenageur(
        Environment.TEST, date(2024, 12, 25), "524335262"
    )  # FRTSL

    # Mock successful submission
    responses.post(
        "http://localhost:8088/api/elec/provision-certificates-qualicharge/bulk-create/",
        status=201,
    )

    # Pretend to have only two amenageurs to speed up test execution
    monkeypatch.setattr(
        tiruert_submit, "get_amenageurs_siren", lambda _: ["891118473", "524335262"]
    )

    tiruert_submit.tiruert_for_month(Environment.TEST, year=2024, month=12)
    with indicators_db_engine.connect() as connection:
        result = connection.execute(
            text(
                "SELECT * FROM test "
                "WHERE code = 'tirue' "
                "AND level = 6 "
                "AND period = 'm' "
            )
        )
    # We should have saved only a single for for FRPD1 over this period
    records = result.all()
    expected = 2
    assert len(records) == expected
