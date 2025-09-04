"""Statid and dynamic rule parameters for Expectations."""

from pydantic import BaseModel


class QARule(BaseModel):
    """Model for rules."""

    code: str
    params: dict


# static parameters
POWU = QARule(code="POWU", params={"max_power_kw": 4000.0})
POWL = QARule(code="POWL", params={"min_power_kw": 1.3})
CRDS = QARule(
    code="CRDS",
    params={
        "lon_max": 10.0,
        "lon_min": -5.0,
        "lat_max": 52.0,
        "lat_min": 41.0,
    },
)
PDCM = QARule(
    code="PDCM",
    params={
        "max_number_of_pdc_per_station": 50,
        "threshold_percent": 0.01,
    },
)
LOCP = QARule(code="LOCP", params={"ratio_stations_per_location": 1.5})
NE10 = QARule(code="NE10", params={"threshold_percent": 0.1})


# dynamic parameters
ENEU = QARule(code="ENEU", params={"max_energy_kwh": 1000.0})
