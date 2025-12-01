"""
SMZ3 (Super Metroid/ALTTP Combo) Randomizer service.

This service handles generation of SMZ3 combo randomizer seeds via samus.link API.
"""

import logging
from typing import Dict, Any, Optional
import httpx

from plugins.builtin._randomizer_base import RandomizerResult

logger = logging.getLogger(__name__)

# Default SMZ3 settings for seed generation
DEFAULT_SMZ3_SETTINGS = {
    "logic": "normal",
    "mode": "normal",
    "goal": "defeatBoth",
    "itemPlacement": "major",
    "swordLocation": "randomized",
    "morphLocation": "original",
}


class SMZ3Service:
    """
    Service for SMZ3 Combo Randomizer.

    Generates seeds for Super Metroid and A Link to the Past combo randomizer
    via the samus.link API.

    Security Note:
    The baseurl parameter is NOT exposed via API endpoints and is only
    used internally with trusted default values. If this parameter were to
    be exposed to user input in the future, URL validation must be added
    to prevent SSRF attacks. See application/utils/url_validator.py.
    """

    def __init__(self):
        """Initialize the SMZ3 service."""
        pass

    async def generate(
        self,
        settings: Dict[str, Any],
        baseurl: str = "https://samus.link",
        tournament: bool = True,
        spoilers: bool = False,
        spoiler_key: Optional[str] = None,
    ) -> RandomizerResult:
        """
        Generate an SMZ3 combo randomizer seed.

        Args:
            settings: Dictionary of randomizer settings
            baseurl: Base URL for the API (default: https://samus.link)
                WARNING: This parameter should NEVER be exposed to user input without
                proper URL validation to prevent SSRF attacks. Currently only used
                with trusted default values.
            tournament: Whether this is a tournament/race seed (default: True)
            spoilers: Whether to generate spoiler log (default: False)
            spoiler_key: Optional key for spoiler log access

        Returns:
            RandomizerResult: The generated seed information

        Raises:
            httpx.HTTPError: If the API request fails
        """
        # Set race mode
        settings["race"] = "true" if tournament else "false"

        # Add spoiler key if requested
        if spoilers and spoiler_key:
            settings["spoilerKey"] = spoiler_key

        logger.info("Generating SMZ3 seed with race=%s", tournament)

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{baseurl}/api/randomize", json=settings, timeout=60.0
            )
            response.raise_for_status()
            result = response.json()

        # Extract data from response
        slug_id = result.get("slug", result.get("id", "unknown"))
        guid = result.get("guid", slug_id)

        seed_url = f"{baseurl}/seed/{slug_id}"

        # Construct spoiler URL if applicable
        spoiler_url = None
        if spoilers and spoiler_key and guid:
            spoiler_url = f"{baseurl}/api/spoiler/{guid}?key={spoiler_key}&yaml=true"

        logger.info("Generated SMZ3 seed with slug %s", slug_id)

        return RandomizerResult(
            url=seed_url,
            hash_id=slug_id,
            settings=settings,
            randomizer="smz3",
            permalink=seed_url,
            spoiler_url=spoiler_url,
            metadata={"guid": guid, "slug": slug_id, **result},
        )
