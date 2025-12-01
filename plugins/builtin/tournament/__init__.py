"""
Tournament Plugin for SahaBot2.

This plugin provides live tournament management functionality including:
- Tournament creation and management
- Match scheduling
- Crew signups and management
- RaceTime.gg integration for race rooms
- SpeedGaming.org schedule sync

This is a built-in plugin that ships with SahaBot2.

Usage:
    from plugins.builtin.tournament import TournamentPlugin
    from plugins.builtin.tournament.models import Tournament, Match
    from plugins.builtin.tournament.services import TournamentService
    from plugins.builtin.tournament.events import TournamentCreatedEvent
"""

from plugins.builtin.tournament.plugin import TournamentPlugin

__all__ = ["TournamentPlugin"]
