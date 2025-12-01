"""
SpeedGaming Plugin for SahaBot2.

Provides SpeedGaming.org integration including:
- Schedule sync and match import
- Player and crew member matching
- Episode ETL (Extract, Transform, Load)
"""

from plugins.builtin.speedgaming.plugin import SpeedGamingPlugin

__all__ = ["SpeedGamingPlugin"]
