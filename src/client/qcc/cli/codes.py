"""QualiCharge API client CLI codes modules ."""

from enum import IntEnum


class QCCExitCodes(IntEnum):
    """QCC CLI exit codes."""

    OK = 0
    PARAMETER_EXCEPTION = 1
    API_EXCEPTION = 2
