"""
Tournament plugin event types.

This module re-exports tournament-related event types from the core application.
These events are used for tournament, match, and crew operations.
"""

from application.events.types import (
    # Tournament events
    TournamentCreatedEvent,
    TournamentUpdatedEvent,
    TournamentDeletedEvent,
    TournamentStartedEvent,
    TournamentEndedEvent,
    # Match events
    MatchScheduledEvent,
    MatchUpdatedEvent,
    MatchDeletedEvent,
    MatchCompletedEvent,
    MatchFinishedEvent,
    TournamentMatchSettingsSubmittedEvent,
    # Crew events
    CrewAddedEvent,
    CrewApprovedEvent,
    CrewRemovedEvent,
)

__all__ = [
    # Tournament events
    "TournamentCreatedEvent",
    "TournamentUpdatedEvent",
    "TournamentDeletedEvent",
    "TournamentStartedEvent",
    "TournamentEndedEvent",
    # Match events
    "MatchScheduledEvent",
    "MatchUpdatedEvent",
    "MatchDeletedEvent",
    "MatchCompletedEvent",
    "MatchFinishedEvent",
    "TournamentMatchSettingsSubmittedEvent",
    # Crew events
    "CrewAddedEvent",
    "CrewApprovedEvent",
    "CrewRemovedEvent",
]
