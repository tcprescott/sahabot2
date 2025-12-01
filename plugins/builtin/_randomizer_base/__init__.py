"""
Shared infrastructure for randomizer plugins.

This module provides base classes and utilities that all randomizer plugins
can use to ensure consistent behavior and reduce code duplication.
"""

from plugins.builtin._randomizer_base.base_randomizer_plugin import (
    BaseRandomizerPlugin,
)
from plugins.builtin._randomizer_base.result import RandomizerResult

__all__ = [
    "BaseRandomizerPlugin",
    "RandomizerResult",
]
