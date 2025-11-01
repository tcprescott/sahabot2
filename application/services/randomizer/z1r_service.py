"""
Zelda 1 Randomizer (Z1R) service.

This service handles generation of The Legend of Zelda randomizer seeds.
"""

import logging
import random
from typing import Optional
from .randomizer_service import RandomizerResult

logger = logging.getLogger(__name__)


class Z1RService:
    """
    Service for Zelda 1 Randomizer.

    Generates seeds for The Legend of Zelda (NES) randomizer.
    """

    def __init__(self):
        """Initialize the Z1R service."""
        pass

    async def generate(self, flags: Optional[str] = None) -> RandomizerResult:
        """
        Generate a Zelda 1 randomizer seed.

        Args:
            flags: Optional flags string for the randomizer

        Returns:
            RandomizerResult: The generated seed information
        """
        seed = random.randint(0, 8999999999999999999)

        logger.info("Generated Z1R seed %s with flags: %s", seed, flags)

        # Z1R URL would be constructed here if there's a web interface
        # For now, we just return the seed and flags
        return RandomizerResult(
            url=f"https://zeldarandomizer.com/seed/{seed}",
            hash_id=str(seed),
            settings={'flags': flags} if flags else {},
            randomizer='z1r',
            metadata={'seed': seed, 'flags': flags}
        )
