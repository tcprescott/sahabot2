"""
Super Mario Bros 3 Randomizer (SMB3R) service.

DEPRECATED: This module is a backward-compatibility re-export.
Import from plugins.builtin.smb3r.services instead.

This service handles generation of Super Mario Bros 3 randomizer seeds.
"""

# Re-export from plugin for backward compatibility
from plugins.builtin.smb3r.services.smb3r_service import SMB3RService

__all__ = ["SMB3RService"]
