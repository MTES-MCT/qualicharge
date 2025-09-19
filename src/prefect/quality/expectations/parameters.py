"""Statid and dynamic rule parameters for Expectations."""

from pydantic import BaseModel


class QARule(BaseModel):
    """Model for rules."""

    code: str
    params: dict


# static parameters
POWU = QARule(code="POWU", params={"max_power_kw": 4000.0})
POWL = QARule(code="POWL", params={"min_power_kw": 1.3})
CRDF = QARule(
    code="CRDF",
    params={"max_lon": 10.0, "min_lon": -5.0, "max_lat": 52.0, "min_lat": 41.0},
)
PDCM = QARule(
    code="PDCM",
    params={"max_pdc_per_station": 50, "threshold_percent": 0.01},
)
LOCP = QARule(code="LOCP", params={"ratio_stations_per_location": 1.5})
NE10 = QARule(code="NE10", params={"threshold_percent": 0.1})


# dynamic parameters
ENEU = QARule(code="ENEU", params={"max_energy_kwh": 1000.0})
DUPS = QARule(code="DUPS", params={"threshold_percent": 0.001})
OVRS = QARule(code="OVRS", params={"max_sessions_per_day": 60})
LONS = QARule(
    code="LONS", params={"max_days_per_session": "3 day", "threshold_percent": 0.001}
)
FRES = QARule(code="FRES", params={"max_duration_day": 15})
