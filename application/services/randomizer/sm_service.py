"""
Super Metroid Randomizer (SM) service.

This service handles generation of Super Metroid randomizer seeds via:
- VARIA randomizer (sm.samus.link API)
- DASH randomizer (dashrando.net API)
"""

import logging
from typing import Dict, Any, Optional, Literal
import httpx
from .randomizer_service import RandomizerResult

logger = logging.getLogger(__name__)

# Type alias for randomizer types
SMRandomizerType = Literal['varia', 'dash', 'total', 'multiworld']


class SMService:
    """
    Service for Super Metroid Randomizer.

    Supports multiple SM randomizer types:
    - VARIA: Standard Super Metroid randomizer (sm.samus.link)
    - DASH: DASH randomizer with area rando (dashrando.net)
    - Total: Full randomization (DASH with all options)
    - Multiworld: Multi-player team seeds
    """

    def __init__(self):
        """Initialize the SM service."""
        self.varia_baseurl = "https://sm.samus.link"
        self.dash_baseurl = "https://dashrando.net"

    async def generate_varia(
        self,
        settings: Dict[str, Any],
        tournament: bool = True,
        spoilers: bool = False,
        spoiler_key: Optional[str] = None
    ) -> RandomizerResult:
        """
        Generate a VARIA Super Metroid randomizer seed.

        Args:
            settings: Dictionary of VARIA randomizer settings
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

        logger.info("Generating VARIA seed with race=%s", tournament)

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.varia_baseurl}/api/randomize",
                json=settings,
                timeout=60.0
            )
            response.raise_for_status()
            result = response.json()

        # Extract data from response
        slug_id = result.get('slug', result.get('id', 'unknown'))
        guid = result.get('guid', slug_id)

        seed_url = f"{self.varia_baseurl}/seed/{slug_id}"

        # Construct spoiler URL if applicable
        spoiler_url = None
        if spoilers and spoiler_key and guid:
            spoiler_url = f"{self.varia_baseurl}/api/spoiler/{guid}?key={spoiler_key}&yaml=true"

        logger.info("Generated VARIA seed with slug %s", slug_id)

        return RandomizerResult(
            url=seed_url,
            hash_id=slug_id,
            settings=settings,
            randomizer='sm-varia',
            permalink=seed_url,
            spoiler_url=spoiler_url,
            metadata={
                'guid': guid,
                'slug': slug_id,
                'type': 'varia',
                **result
            }
        )

    async def generate_dash(
        self,
        settings: Dict[str, Any],
        tournament: bool = True,
        spoilers: bool = False
    ) -> RandomizerResult:
        """
        Generate a DASH Super Metroid randomizer seed.

        Args:
            settings: Dictionary of DASH randomizer settings
            tournament: Whether this is a tournament/race seed (default: True)
            spoilers: Whether to generate spoiler log (default: False)

        Returns:
            RandomizerResult: The generated seed information

        Raises:
            httpx.HTTPError: If the API request fails
        """
        # DASH API expects different parameter names
        payload = {
            **settings,
            'race': tournament
        }

        logger.info("Generating DASH seed with race=%s", tournament)

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.dash_baseurl}/api/generate",
                json=payload,
                timeout=60.0
            )
            response.raise_for_status()
            result = response.json()

        # Extract data from response
        seed_id = result.get('id', result.get('seed', 'unknown'))
        hash_value = result.get('hash', seed_id)

        seed_url = f"{self.dash_baseurl}/seed/{seed_id}"

        # DASH spoiler log handling
        spoiler_url = None
        if spoilers and result.get('spoiler_url'):
            spoiler_url = f"{self.dash_baseurl}{result['spoiler_url']}"

        logger.info("Generated DASH seed with ID %s", seed_id)

        return RandomizerResult(
            url=seed_url,
            hash_id=hash_value,
            settings=settings,
            randomizer='sm-dash',
            permalink=seed_url,
            spoiler_url=spoiler_url,
            metadata={
                'id': seed_id,
                'hash': hash_value,
                'type': 'dash',
                **result
            }
        )

    async def generate(
        self,
        settings: Dict[str, Any],
        randomizer_type: SMRandomizerType = 'varia',
        tournament: bool = True,
        spoilers: bool = False,
        spoiler_key: Optional[str] = None
    ) -> RandomizerResult:
        """
        Generate a Super Metroid randomizer seed.

        This is the main entry point that routes to the appropriate generator.

        Args:
            settings: Dictionary of randomizer settings
            randomizer_type: Type of SM randomizer ('varia', 'dash', 'total', 'multiworld')
            tournament: Whether this is a tournament/race seed (default: True)
            spoilers: Whether to generate spoiler log (default: False)
            spoiler_key: Optional key for spoiler log access (VARIA only)

        Returns:
            RandomizerResult: The generated seed information

        Raises:
            httpx.HTTPError: If the API request fails
            ValueError: If randomizer_type is not recognized
        """
        if randomizer_type == 'varia':
            return await self.generate_varia(settings, tournament, spoilers, spoiler_key)
        elif randomizer_type == 'dash':
            return await self.generate_dash(settings, tournament, spoilers)
        elif randomizer_type == 'total':
            # Total randomization uses DASH with all options enabled
            total_settings = {
                **settings,
                'area_rando': True,
                'major_minor_split': True,
                'boss_rando': True
            }
            return await self.generate_dash(total_settings, tournament, spoilers)
        elif randomizer_type == 'multiworld':
            # Multiworld uses VARIA with multiworld settings
            multiworld_settings = {
                **settings,
                'multiworld': True
            }
            return await self.generate_varia(multiworld_settings, tournament, spoilers, spoiler_key)
        else:
            raise ValueError(
                f"Unknown SM randomizer type: {randomizer_type}. "
                f"Supported types: 'varia', 'dash', 'total', 'multiworld'"
            )
