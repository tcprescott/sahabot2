"""
Tournament plugin events.

This module exports tournament-related event types defined in the plugin.
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
    CrewUnapprovedEvent,
    CrewRemovedEvent,
    MatchChannelAssignedEvent,
    MatchChannelUnassignedEvent,
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
    "CrewUnapprovedEvent",
    "CrewRemovedEvent",
    "MatchChannelAssignedEvent",
    "MatchChannelUnassignedEvent",
]
