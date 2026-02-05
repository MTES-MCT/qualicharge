"""Static and dynamic rule parameters for Expectations."""

from pydantic import BaseModel


class QARule(BaseModel):
    """Model for rules."""

    code: str
    params: dict


HISTORY_STRATEGY_FIELD: str = "mean"
IS_DC: str = """(
puissance_nominale >= 50
OR prise_type_combo_ccs
OR prise_type_chademo
)"""

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

# sessions parameters
DUPS = QARule(code="DUPS", params={"threshold_percent": 0.001})
OVRS = QARule(code="OVRS", params={"max_sessions_per_day": 60})
LONS = QARule(
    code="LONS", params={"max_days_per_session": "3 day", "threshold_percent": 0.001}
)
FRES = QARule(code="FRES", params={"max_duration_day": 15})
NEGS = QARule(code="NEGS", params={})
session_p = [DUPS, OVRS, LONS, FRES, NEGS]

# energy parameters
# Maximum energy : max_energy = puissance_nominale * session_duration
# Unacceptable energy : if energy > highest_energy_kwh
# Excessive energy : if energy > excess_coef * max_energy and > excess_threshold_kWh
# Abnormal energy : if energy > abnormal_coef * max_energy
ENERGY = {"highest_energy_kwh": 1000, "lowest_energy_kwh": 1}
ENEX = QARule(code="ENEX", params={"excess_coef": 2, "excess_threshold_kWh": 50})
ENEA = QARule(code="ENEA", params={"abnormal_coef": 1.1, "threshold_percent": 0.001})
ENEU = QARule(code="ENEU", params={})
ODUR = QARule(code="ODUR", params={"threshold_percent": 0.001})
energy_p = [ENEX, ENEA, ENEU, ODUR]

# statuses parameters
DUPT = QARule(code="DUPT", params={"threshold_percent": 0.01})
FRET = QARule(code="FRET", params={"mean_duration_second": 300})
FTRT = QARule(code="FTRT", params={})
ERRT = QARule(code="ERRT", params={})
OVRT = QARule(code="OVRT", params={"max_statuses_per_day": 1440})
status_p = [DUPT, FRET, FTRT, ERRT, OVRT]

# pdc-status parameters
INAC = QARule(
    code="INAC", params={"inactivity_duration": "1 month", "threshold_percent": 0.02}
)
DECL = QARule(code="DECL", params={"threshold_percent": 0.02})
pdc_status_p = [INAC, DECL]

# statuses-sessions consistency parameters
RATS = QARule(
    code="RATS",
    params={"ratio_statuses_per_session_min": 1, "ratio_statuses_per_session_max": 30},
)
OCCT = QARule(code="OCCT", params={"threshold_percent": 0.2})
SEST = QARule(code="SEST", params={"threshold_percent": 0.01})
session_status_p = [RATS, OCCT, SEST]

# evaluable parameters (check a threshold)
eval_p = [
    PDCM,
    LOCP,
    NE10,
    ODUR,
    ENEA,
    DUPS,
    LONS,
    FRES,
    DUPT,
    FRET,
    RATS,
    OCCT,
    SEST,
    INAC,
    DECL,
]

# parameters categories
EVALUABLE_PARAMS = [params.code for params in eval_p]
SESSION_PARAMS = [params.code for params in session_p + energy_p + session_status_p]
STATUS_PARAMS = [params.code for params in status_p + pdc_status_p]
