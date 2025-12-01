"""
RandomizerResult dataclass.

This module provides the shared result type for all randomizer plugins.
"""

from dataclasses import dataclass
from typing import Optional, Dict, Any


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


__all__ = ["RandomizerResult"]
