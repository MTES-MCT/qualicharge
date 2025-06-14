"""test_s3"""

import os

import pandas as pd
import pytest
from freezegun import freeze_time
from prefect.client.schemas.objects import StateType

from cooling import IfExistStrategy
from cooling.sessions import extract_old_sessions
from indicators.types import Environment

if __name__ == "__main__":
    print("ok")
