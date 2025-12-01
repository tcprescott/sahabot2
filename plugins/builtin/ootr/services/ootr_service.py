"""
Ocarina of Time Randomizer (OOTR) service.

This service handles generation of Ocarina of Time randomizer seeds via API.
"""

import logging
from typing import Dict, Any, Optional
import httpx
from config import settings

from plugins.builtin._randomizer_base import RandomizerResult

logger = logging.getLogger(__name__)


class OOTRService:
    """
    Service for Ocarina of Time Randomizer.

    Generates seeds for Ocarina of Time randomizer via the official API.
    """

    BASE_URL = "https://ootrandomizer.com"

    def __init__(self):
        """Initialize the OOTR service."""
        pass

    async def generate(
        self,
        settings_dict: Dict[str, Any],
        version: str = "6.1.0",
        encrypt: bool = True,
    ) -> RandomizerResult:
        """
        Generate an Ocarina of Time randomizer seed.

        Args:
            settings_dict: Dictionary of randomizer settings
            version: OoTR version to use (default: '6.1.0')
            encrypt: Whether to encrypt the seed (default: True)

        Returns:
            RandomizerResult: The generated seed information

        Raises:
            httpx.HTTPError: If the API request fails
        """
        api_key = getattr(settings, "OOTR_API_KEY", None)
        if not api_key:
            logger.warning("OOTR_API_KEY not configured, seed generation may fail")

        params = {"version": version, "encrypt": str(encrypt).lower()}

        if api_key:
            params["key"] = api_key

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.BASE_URL}/api/sglive/seed/create",
                json=settings_dict,
                params=params,
                timeout=30.0,
            )
            response.raise_for_status()
            result = response.json()

        logger.info("Generated OOTR seed with version %s", version)

        # Extract relevant data from result
        seed_id = result.get("id", result.get("seed_id", "unknown"))

        return RandomizerResult(
            url=result.get("url", f"{self.BASE_URL}/seed/{seed_id}"),
            hash_id=str(seed_id),
            settings=settings_dict,
            randomizer="ootr",
            permalink=result.get("permalink"),
            metadata=result,
        )
