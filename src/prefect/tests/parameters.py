"""Common parameters for tests."""

from indicators.models import Level  # type: ignore

# number of departments
N_DPTS = 109

# cumulate number of national(1), regions, departments, EPCI, city
N_NAT_REG_DPT_EPCI_CITY = 36465

PARAMETERS_CHUNK = [10, 50, 100, 500]

PARAM_FLOW = [
    (
        Level.CITY,
        "SELECT COUNT(*) FROM City",
        ["75056", "13055", "69123"],
    ),
    (
        Level.EPCI,
        "SELECT COUNT(*) FROM EPCI",
        ["200054781", "200054807", "200046977"],
    ),
    (
        Level.DEPARTMENT,
        "SELECT COUNT(*) FROM Department",
        ["59", "75", "13"],
    ),
    (
        Level.REGION,
        "SELECT COUNT(*) FROM Region",
        ["11", "84", "75"],
    ),
]

PARAM_VALUE = [
    (
        Level.CITY,
        "SELECT id FROM City WHERE name IN ('Paris', 'Marseille', 'Lyon')",
    ),
    (
        Level.EPCI,
        "SELECT id FROM EPCI WHERE code IN ('200054781', '200054807', '200046977')",
    ),
    (
        Level.DEPARTMENT,
        "SELECT id FROM Department WHERE code IN ('59', '75', '13')",
    ),
    (
        Level.REGION,
        "SELECT id FROM Region WHERE code IN ('11', '84', '75')",
    ),
]
