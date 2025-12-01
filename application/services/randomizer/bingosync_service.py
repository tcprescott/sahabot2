"""
Bingosync service for generating bingo cards.

DEPRECATED: This module is a backward-compatibility re-export.
Import from plugins.builtin.bingosync.services instead.

This service handles creation of Bingosync rooms and bingo card generation.
"""

# Re-export from plugin for backward compatibility
from plugins.builtin.bingosync.services.bingosync_service import BingosyncService

__all__ = ["BingosyncService"]
