"""
Final Fantasy Randomizer (FFR) service.

This service handles generation of Final Fantasy randomizer seeds.
"""

import logging
import random
from typing import Dict, Any
from .randomizer_service import RandomizerResult

logger = logging.getLogger(__name__)


class FFRService:
    """
    Service for Final Fantasy Randomizer.

    Generates seeds for Final Fantasy (NES) randomizer.
    """

    def __init__(self):
        """Initialize the FFR service."""
        pass

    async def generate(self, flags: str = "", seed: int = None) -> RandomizerResult:
        """
        Generate a Final Fantasy randomizer seed.

        Args:
            flags: Flags string for the randomizer
            seed: Optional specific seed to use (random if not provided)

        Returns:
            RandomizerResult: The generated seed information
        """
        if seed is None:
            seed = random.randint(0, 2147483647)

        url = f"https://finalfantasyrandomizer.com/Randomize?s={seed}&f={flags}"

        logger.info("Generated FFR seed %s with flags: %s", seed, flags)

        return RandomizerResult(
            url=url,
            hash_id=str(seed),
            settings={'flags': flags, 'seed': seed},
            randomizer='ffr',
            permalink=url,
        )
