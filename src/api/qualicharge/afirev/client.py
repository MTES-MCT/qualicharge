"""QualiCharge afirev API client."""

import logging
from typing import List

import httpx
from pydantic import HttpUrl, ValidationError

from ..conf import settings
from .models import AfirevPrefix, AfirevPrefixAPIResponse

logger = logging.getLogger(__name__)


class AfirevClientException(Exception):
    """AFIREV HTTP API client exception."""


class AfirevClient:
    """AFIREV API client."""

    def __init__(
        self,
        api_root_url: HttpUrl = settings.AFIREV_API_ROOL_URL,
    ) -> None:
        """Setup API client."""
        self.client = httpx.Client(base_url=str(api_root_url))

    def prefixes(self) -> List[AfirevPrefix]:
        """Fetch all prefixes."""
        logger.info("Will fetch prefixes from AFIREV's API…")
        response = self.client.get("/prefixes")
        response.raise_for_status()

        # Parse the response
        try:
            prefixes = AfirevPrefixAPIResponse.model_validate_json(response.text)
        except ValidationError as err:
            raise AfirevClientException("Invalid AFIREV API response format.") from err

        logger.info("Fetched %d prefixes from AFIREV API.", prefixes.total)

        return prefixes.data
