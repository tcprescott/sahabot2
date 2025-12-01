"""
Tournament Plugin for SahaBot2.

This plugin provides live tournament management functionality including:
- Tournament creation and management
- Match scheduling
- Crew signups and management
- RaceTime.gg integration for race rooms
- SpeedGaming.org schedule sync

This is a built-in plugin that ships with SahaBot2.
"""

from plugins.builtin.tournament.plugin import TournamentPlugin

__all__ = ["TournamentPlugin"]
