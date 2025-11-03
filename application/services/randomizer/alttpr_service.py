"""
A Link to the Past Randomizer (ALTTPR) service.

This service handles generation of ALTTPR seeds via the official API.
"""

import logging
from typing import Dict, Any, Optional
import httpx
from config import settings
from .randomizer_service import RandomizerResult

logger = logging.getLogger(__name__)


class ALTTPRService:
    """
    Service for A Link to the Past Randomizer.

    Generates seeds for ALTTPR via the official API at alttpr.com.
    """

    def __init__(self):
        """Initialize the ALTTPR service."""
        pass

    async def generate(
        self,
        settings_dict: Dict[str, Any],
        baseurl: Optional[str] = None,
        endpoint: str = "/api/randomizer",
        tournament: bool = True,
        spoilers: str = "off",
        allow_quickswap: bool = False
    ) -> RandomizerResult:
        """
        Generate an ALTTPR seed.

        Args:
            settings_dict: Dictionary of randomizer settings
            baseurl: Base URL for the API (default: from config or https://alttpr.com)
            endpoint: API endpoint to use (default: /api/randomizer)
            tournament: Whether this is a tournament seed (default: True)
            spoilers: Spoiler level ('on', 'off', 'generate') (default: 'off')
            allow_quickswap: Whether to allow quick swap (default: False)

        Returns:
            RandomizerResult: The generated seed information

        Raises:
            httpx.HTTPError: If the API request fails
        """
        if baseurl is None:
            baseurl = getattr(settings, 'ALTTPR_BASEURL', 'https://alttpr.com')

        # Apply additional settings
        settings_dict['tournament'] = tournament
        settings_dict['spoilers'] = spoilers
        if 'allow_quickswap' not in settings_dict:
            settings_dict['allow_quickswap'] = allow_quickswap

        url = f"{baseurl}{endpoint}"

        logger.info("Generating ALTTPR seed with endpoint %s", endpoint)

        async with httpx.AsyncClient() as client:
            response = await client.post(
                url,
                json=settings_dict,
                timeout=60.0
            )
            response.raise_for_status()
            result = response.json()

        # Extract data from response
        hash_id = result.get('hash', result.get('seed', {}).get('hash', 'unknown'))
        permalink = result.get('permalink', result.get('url'))

        logger.info("Generated ALTTPR seed with hash %s", hash_id)

        return RandomizerResult(
            url=permalink,
            hash_id=hash_id,
            settings=settings_dict,
            randomizer='alttpr',
            permalink=permalink,
            spoiler_url=result.get('spoiler', {}).get('download') if spoilers != 'off' else None,
            metadata=result
        )

    async def generate_from_preset(
        self,
        preset_name: str,
        user_id: int,
        tournament: bool = True,
        spoilers: str = "off",
        allow_quickswap: bool = False
    ) -> RandomizerResult:
        """
        Generate an ALTTPR seed from a preset.

        Args:
            preset_name: Name of the preset to use
            user_id: User ID requesting the preset
            tournament: Whether this is a tournament seed (default: True)
            spoilers: Spoiler level ('on', 'off', 'generate') (default: 'off')
            allow_quickswap: Allow quickswap (default: False)

        Returns:
            RandomizerResult: The generated seed information

        Raises:
            ValueError: If preset is not found
            PermissionError: If user cannot access preset
            httpx.HTTPError: If the API request fails
        """
        from application.repositories.randomizer_preset_repository import RandomizerPresetRepository

        # Load preset from database
        preset_repo = RandomizerPresetRepository()

        # Get preset by name
        preset = await preset_repo.get_by_name(
            randomizer='alttpr',
            name=preset_name
        )

        if not preset:
            raise ValueError(f"Preset '{preset_name}' not found")

        # Check if user can access preset (must be public or owned by user)
        if not preset.is_public and preset.user_id != user_id:
            logger.warning(
                "User %s attempted to access private preset %s owned by %s",
                user_id, preset_name, preset.user_id
            )
            raise PermissionError(f"Not authorized to access preset '{preset_name}'")

        # Extract settings from preset
        settings_dict = preset.settings.get('settings', preset.settings)

        # Generate seed using preset settings
        return await self.generate(
            settings_dict=settings_dict,
            tournament=tournament,
            spoilers=spoilers,
            allow_quickswap=allow_quickswap
        )

