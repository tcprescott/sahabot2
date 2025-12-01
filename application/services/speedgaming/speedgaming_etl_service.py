"""
SpeedGaming ETL (Extract, Transform, Load) service.

DEPRECATED: This module is a backward-compatibility re-export.
Import from plugins.builtin.speedgaming.services instead.

This service handles importing SpeedGaming episodes into the Match table.
"""

# Re-export from plugin for backward compatibility
from plugins.builtin.speedgaming.services.speedgaming_etl_service import (
    SpeedGamingETLService,
)

__all__ = ["SpeedGamingETLService"]
