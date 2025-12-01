"""
RandomizerResult dataclass.

This module provides the shared result type for all randomizer plugins.
"""

# Re-export from core randomizer service
from application.services.randomizer.randomizer_service import RandomizerResult

__all__ = ["RandomizerResult"]
