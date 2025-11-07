"""
Avianart randomizer service.

This service handles generation of ALTTPR door randomizer seeds via the
Avianart API (Hi, I'm Cody's door randomizer generator).
"""

import logging
import asyncio
from typing import Optional
import httpx
from .randomizer_service import RandomizerResult

logger = logging.getLogger(__name__)


class AvianartService:
    """
    Service for Avianart door randomizer.

    Generates ALTTPR door randomizer seeds via the Avianart API at avianart.games.
    This randomizer uses presets but does not store them in the database - users
    must specify the preset name when generating.
    """

    BASE_URL = "https://avianart.games"
    POLL_INTERVAL_SECONDS = 5
    MAX_POLL_ATTEMPTS = 24  # 24 attempts * 5 seconds = 2 minutes max

    def __init__(self):
        """Initialize the Avianart service."""
        pass

    async def generate(
        self,
        preset: str,
        race: bool = True,
    ) -> RandomizerResult:
        """
        Generate an Avianart door randomizer seed.

        Args:
            preset: Name of the Avianart preset to use
            race: Whether this is a race seed (default: True)

        Returns:
            RandomizerResult: The generated seed information

        Raises:
            ValueError: If preset is not provided or generation fails
            httpx.HTTPError: If the API request fails
            TimeoutError: If seed generation takes too long
        """
        if not preset:
            raise ValueError("Preset name is required for Avianart generation")

        logger.info("Generating Avianart seed with preset %s (race=%s)", preset, race)

        # Prepare payload for generation
        payload = [{"args": {"race": race}}]

        async with httpx.AsyncClient(timeout=60.0) as client:
            # Step 1: Initiate seed generation
            response = await client.post(
                f"{self.BASE_URL}/api.php?action=generate&preset={preset}",
                json=payload
            )
            response.raise_for_status()
            result = response.json()

            hash_id = result['response']['hash']
            logger.info("Avianart seed generation started with hash %s", hash_id)

            # Step 2: Poll until generation is complete
            attempts = 0
            while attempts < self.MAX_POLL_ATTEMPTS:
                await asyncio.sleep(self.POLL_INTERVAL_SECONDS)
                attempts += 1

                response = await client.get(
                    f"{self.BASE_URL}/api.php?action=permlink&hash={hash_id}"
                )
                response.raise_for_status()
                result = response.json()

                status = result['response'].get('status', 'finished')

                if status == 'finished':
                    logger.info("Avianart seed %s generated successfully after %s attempts", hash_id, attempts)
                    break

                if status == 'failure':
                    error_msg = result['response'].get('message', 'Unknown error')
                    logger.error("Avianart seed generation failed: %s", error_msg)
                    raise ValueError(f"Failed to generate Avianart seed: {error_msg}")

                logger.debug("Avianart seed %s still generating (attempt %s/%s, status=%s)",
                            hash_id, attempts, self.MAX_POLL_ATTEMPTS, status)

            if attempts >= self.MAX_POLL_ATTEMPTS:
                logger.error("Avianart seed generation timed out after %s attempts", attempts)
                raise TimeoutError(
                    f"Seed generation timed out after {attempts * self.POLL_INTERVAL_SECONDS} seconds"
                )

        # Extract file select code from spoiler
        file_select_code = self._extract_file_select_code(result)
        version = result['response']['spoiler']['meta'].get('version', 'unknown')
        url = f"{self.BASE_URL}/perm/{hash_id}"

        logger.info("Generated Avianart seed %s (version %s)", hash_id, version)

        return RandomizerResult(
            url=url,
            hash_id=hash_id,
            settings={'preset': preset, 'race': race},
            randomizer='avianart',
            permalink=url,
            metadata={
                'file_select_code': file_select_code,
                'version': version,
                'preset': preset,
                'spoiler': result['response'].get('spoiler')
            }
        )

    def _extract_file_select_code(self, result: dict) -> list[str]:
        """
        Extract and normalize file select code from API result.

        The Avianart API returns codes that need to be mapped to standard names.

        Args:
            result: API response containing spoiler data

        Returns:
            List of 5 file select code items
        """
        file_select_code_str = result['response']['spoiler']['meta']['hash']
        code = list(file_select_code_str.split(', '))

        # Map Avianart names to standard SahasrahBot names
        code_map = {
            'Bomb': 'Bombs',
            'Powder': 'Magic Powder',
            'Rod': 'Ice Rod',
            'Ocarina': 'Flute',
            'Bug Net': 'Bugnet',
            'Bottle': 'Empty Bottle',
            'Potion': 'Green Potion',
            'Cane': 'Somaria',
            'Pearl': 'Moon Pearl',
            'Key': 'Big Key'
        }

        normalized_code = [code_map.get(item, item) for item in code]

        # Return first 5 items (standard file select code length)
        return normalized_code[:5]
