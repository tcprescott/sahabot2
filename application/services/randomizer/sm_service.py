"""
Super Metroid Randomizer (SM) service.

This service handles generation of Super Metroid randomizer seeds via SM.samus.link API.
"""

import logging
from typing import Dict, Any, Optional
import httpx
from .randomizer_service import RandomizerResult

logger = logging.getLogger(__name__)


class SMService:
    """
    Service for Super Metroid Randomizer.

    Generates seeds for Super Metroid via the sm.samus.link API.
    """

    def __init__(self):
        """Initialize the SM service."""
        pass

    async def generate(
        self,
        settings: Dict[str, Any],
        baseurl: str = "https://sm.samus.link",
        tournament: bool = True,
        spoilers: bool = False,
        spoiler_key: Optional[str] = None
    ) -> RandomizerResult:
        """
        Generate a Super Metroid randomizer seed.

        Args:
            settings: Dictionary of randomizer settings
            baseurl: Base URL for the API (default: https://sm.samus.link)
            tournament: Whether this is a tournament/race seed (default: True)
            spoilers: Whether to generate spoiler log (default: False)
            spoiler_key: Optional key for spoiler log access

        Returns:
            RandomizerResult: The generated seed information

        Raises:
            httpx.HTTPError: If the API request fails
        """
        # Set race mode
        settings['race'] = "true" if tournament else "false"

        # Add spoiler key if requested
        if spoilers and spoiler_key:
            settings['spoilerKey'] = spoiler_key

        logger.info("Generating SM seed with race=%s", tournament)

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{baseurl}/api/randomize",
                json=settings,
                timeout=60.0
            )
            response.raise_for_status()
            result = response.json()

        # Extract data from response
        slug_id = result.get('slug', result.get('id', 'unknown'))
        guid = result.get('guid', slug_id)

        seed_url = f"{baseurl}/seed/{slug_id}"

        # Construct spoiler URL if applicable
        spoiler_url = None
        if spoilers and spoiler_key and guid:
            spoiler_url = f"{baseurl}/api/spoiler/{guid}?key={spoiler_key}&yaml=true"

        logger.info("Generated SM seed with slug %s", slug_id)

        return RandomizerResult(
            url=seed_url,
            hash_id=slug_id,
            settings=settings,
            randomizer='sm',
            permalink=seed_url,
            spoiler_url=spoiler_url,
            metadata={
                'guid': guid,
                'slug': slug_id,
                **result
            }
        )
