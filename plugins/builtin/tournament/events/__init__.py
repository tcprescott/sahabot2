"""
Tournament plugin events.

This module re-exports tournament-related event types from the core application.
In a future phase, these events may be moved directly into the plugin.

For now, this provides a stable import path for plugin-internal use.
"""

from plugins.builtin.tournament.events.types import (
    TournamentCreatedEvent,
    TournamentUpdatedEvent,
    TournamentDeletedEvent,
    TournamentStartedEvent,
    TournamentEndedEvent,
    MatchScheduledEvent,
    MatchUpdatedEvent,
    MatchDeletedEvent,
    MatchCompletedEvent,
    MatchFinishedEvent,
    TournamentMatchSettingsSubmittedEvent,
    CrewAddedEvent,
    CrewApprovedEvent,
    CrewRemovedEvent,
)

__all__ = [
    "TournamentCreatedEvent",
    "TournamentUpdatedEvent",
    "TournamentDeletedEvent",
    "TournamentStartedEvent",
    "TournamentEndedEvent",
    "MatchScheduledEvent",
    "MatchUpdatedEvent",
    "MatchDeletedEvent",
    "MatchCompletedEvent",
    "MatchFinishedEvent",
    "TournamentMatchSettingsSubmittedEvent",
    "CrewAddedEvent",
    "CrewApprovedEvent",
    "CrewRemovedEvent",
]
