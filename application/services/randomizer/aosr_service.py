"""
Aria of Sorrow Randomizer (AOSR) service.

This service handles generation of Castlevania: Aria of Sorrow randomizer seeds.
"""

import logging
import random
from typing import Dict, Any
from .randomizer_service import RandomizerResult

logger = logging.getLogger(__name__)


class AOSRService:
    """
    Service for Aria of Sorrow Randomizer.

    Generates seeds for Castlevania: Aria of Sorrow randomizer.
    """

    def __init__(self):
        """Initialize the AOSR service."""
        pass

    async def generate(self, **kwargs) -> RandomizerResult:
        """
        Generate an Aria of Sorrow randomizer seed.

        Args:
            **kwargs: Settings for the randomizer (passed as URL parameters)

        Returns:
            RandomizerResult: The generated seed information
        """
        seed = random.randint(-2147483648, 2147483647)
        flags = [f"{key}={val}" for (key, val) in kwargs.items()]
        url = f"https://aosrando.surge.sh/?seed={seed}&{'&'.join(flags)}"

        logger.info("Generated AOSR seed %s with flags: %s", seed, flags)

        return RandomizerResult(
            url=url,
            hash_id=str(seed),
            settings=kwargs,
            randomizer="aosr",
            permalink=url,
        )
