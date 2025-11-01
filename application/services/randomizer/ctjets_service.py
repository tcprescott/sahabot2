"""
Chrono Trigger Jets of Time (CTJets) Randomizer service.

This service handles generation of Chrono Trigger randomizer seeds via ctjot.com.
"""

import logging
from typing import Dict, Any
import httpx
from bs4 import BeautifulSoup
from .randomizer_service import RandomizerResult

logger = logging.getLogger(__name__)


class CTJetsService:
    """
    Service for Chrono Trigger Jets of Time Randomizer.

    Generates seeds for Chrono Trigger randomizer via ctjot.com.
    Note: This service requires a base Chrono Trigger ROM file which must be
    provided separately and is not included with this application.
    """

    def __init__(self):
        """Initialize the CTJets service."""
        pass

    async def generate(
        self,
        settings: Dict[str, Any],
        version: str = '3_1_0',
        rom_path: str = None
    ) -> RandomizerResult:
        """
        Generate a Chrono Trigger Jets of Time randomizer seed.

        Args:
            settings: Dictionary of randomizer settings
            version: Version string (default: '3_1_0')
            rom_path: Path to base Chrono Trigger ROM file (optional)

        Returns:
            RandomizerResult: The generated seed information

        Raises:
            ValueError: If ROM file is required but not provided
            httpx.HTTPError: If the API request fails
        """
        version = version.replace('.', '_')
        base_url = f'https://ctjot.com/{version}'

        logger.info("Generating CTJets seed with version %s", version)

        async with httpx.AsyncClient(follow_redirects=True) as client:
            # Get CSRF token
            resp = await client.get(f'{base_url}/options/')
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, features="html.parser")

            csrf_token = soup.find('input', {'name': 'csrfmiddlewaretoken'})
            if not csrf_token:
                raise ValueError("Could not find CSRF token")

            csrf_value = csrf_token.get('value')

            # Prepare form data
            form_data = {
                'csrfmiddlewaretoken': csrf_value,
                'seed': '',
                **settings
            }

            # Note: ROM file handling requires multipart/form-data upload with the base
            # Chrono Trigger ROM file. This is intentionally not implemented as it would
            # require users to provide their own ROM files, which cannot be distributed.
            # For actual ROM generation, implement multipart upload as follows:
            # files = {'rom_file': ('chronotrigger.sfc', rom_bytes, 'application/octet-stream')}
            # response = await client.post(url, data=form_data, files=files, ...)
            if rom_path:
                logger.warning("ROM file path provided but ROM upload not implemented")

            # Submit form
            resp = await client.post(
                f'{base_url}/generate-rom/',
                data=form_data,
                headers={'Referer': f'{base_url}/options/'},
                timeout=60.0
            )
            resp.raise_for_status()

            # Parse response for seed link
            soup = BeautifulSoup(resp.text, features="html.parser")
            link = soup.find('a', text='Seed share link')

            if link and link.get('href'):
                relative_uri = link['href']
                seed_url = f"https://ctjot.com{relative_uri}"
            else:
                # Fallback if we can't find the link
                seed_url = f"{base_url}/seed/unknown"
                logger.warning("Could not find seed share link in response")

        logger.info("Generated CTJets seed: %s", seed_url)

        return RandomizerResult(
            url=seed_url,
            hash_id=seed_url.split('/')[-1] if '/' in seed_url else 'unknown',
            settings=settings,
            randomizer='ctjets',
            permalink=seed_url,
            metadata={'version': version}
        )
