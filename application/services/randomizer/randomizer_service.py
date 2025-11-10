"""
Randomizer service for coordinating different game randomizers.

This service provides a unified interface for accessing various game randomizers.
"""

import logging
from typing import Optional, Dict, Any
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class RandomizerResult:
    """
    Result from a randomizer generation.

    Attributes:
        url: URL to access the generated seed
        hash_id: Unique identifier/hash for the seed
        settings: Dictionary of settings used to generate the seed
        randomizer: Name of the randomizer used
        permalink: Optional permalink to the seed
        spoiler_url: Optional URL to spoiler log
        metadata: Additional metadata specific to the randomizer
    """

    url: str
    hash_id: str
    settings: Dict[str, Any]
    randomizer: str
    permalink: Optional[str] = None
    spoiler_url: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class RandomizerService:
    """
    Main service for coordinating different game randomizers.

    This service acts as a factory and coordinator for various randomizer
    implementations, providing a consistent interface for generating seeds
    across different games.
    """

    def __init__(self):
        """Initialize the randomizer service."""
        self._randomizers = {}

    def get_randomizer(self, name: str):
        """
        Get a randomizer service by name.

        Args:
            name: Name of the randomizer (e.g., 'alttpr', 'sm', 'z1r')

        Returns:
            The randomizer service instance

        Raises:
            ValueError: If randomizer name is not recognized
        """
        name = name.lower()

        # Lazy import to avoid circular dependencies
        if name == "alttpr":
            from .alttpr_service import ALTTPRService

            return ALTTPRService()
        elif name == "aosr":
            from .aosr_service import AOSRService

            return AOSRService()
        elif name == "z1r":
            from .z1r_service import Z1RService

            return Z1RService()
        elif name == "ootr":
            from .ootr_service import OOTRService

            return OOTRService()
        elif name == "ffr":
            from .ffr_service import FFRService

            return FFRService()
        elif name == "smb3r":
            from .smb3r_service import SMB3RService

            return SMB3RService()
        elif name == "sm":
            from .sm_service import SMService

            return SMService()
        elif name == "smz3":
            from .smz3_service import SMZ3Service

            return SMZ3Service()
        elif name == "ctjets" or name == "ct":
            from .ctjets_service import CTJetsService

            return CTJetsService()
        elif name == "bingosync" or name == "bingo":
            from .bingosync_service import BingosyncService

            return BingosyncService()
        elif name == "avianart":
            from .avianart_service import AvianartService

            return AvianartService()
        else:
            raise ValueError(f"Unknown randomizer: {name}")

    def list_randomizers(self) -> list[str]:
        """
        List all available randomizers.

        Returns:
            list[str]: List of randomizer names
        """
        return [
            "alttpr",
            "aosr",
            "z1r",
            "ootr",
            "ffr",
            "smb3r",
            "sm",
            "smz3",
            "ctjets",
            "bingosync",
            "avianart",
        ]
