"""
Bot commands package.

This package contains all Discord bot application commands.
"""

from .test_commands import setup as setup_test_commands
from .mystery_commands import setup as setup_mystery_commands

__all__ = ["setup_test_commands", "setup_mystery_commands"]
