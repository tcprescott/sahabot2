"""
Tournament plugin event types.

This module contains event types for tournament, match, and crew operations.
These events are emitted by the tournament services and handled by listeners.
"""

from dataclasses import dataclass, field
from typing import Optional, List
from application.events.base import EntityEvent, EventPriority


# ============================================================================
# Tournament Events
# ============================================================================


@dataclass(frozen=True)
class TournamentCreatedEvent(EntityEvent):
    """Emitted when a new tournament is created."""

    entity_type: str = field(default="Tournament", init=False)
    tournament_name: Optional[str] = None
    tournament_type: Optional[str] = None


@dataclass(frozen=True)
class TournamentUpdatedEvent(EntityEvent):
    """Emitted when a tournament is updated."""

    entity_type: str = field(default="Tournament", init=False)
    changed_fields: List[str] = field(default_factory=list)


@dataclass(frozen=True)
class TournamentDeletedEvent(EntityEvent):
    """Emitted when a tournament is deleted."""

    entity_type: str = field(default="Tournament", init=False)
    reason: Optional[str] = None


@dataclass(frozen=True)
class TournamentStartedEvent(EntityEvent):
    """Emitted when a tournament officially starts."""

    entity_type: str = field(default="Tournament", init=False)
    tournament_name: Optional[str] = None
    priority: EventPriority = EventPriority.HIGH


@dataclass(frozen=True)
class TournamentEndedEvent(EntityEvent):
    """Emitted when a tournament is completed."""

    entity_type: str = field(default="Tournament", init=False)
    tournament_name: Optional[str] = None
    winner_user_id: Optional[int] = None
    priority: EventPriority = EventPriority.HIGH


# ============================================================================
# Match Events
# ============================================================================


@dataclass(frozen=True)
class MatchScheduledEvent(EntityEvent):
    """Emitted when a match is scheduled."""

    entity_type: str = field(default="MatchSchedule", init=False)
    tournament_id: Optional[int] = None
    scheduled_time: Optional[str] = None  # ISO format
    participant_ids: List[int] = field(default_factory=list)


@dataclass(frozen=True)
class MatchUpdatedEvent(EntityEvent):
    """Emitted when a match is updated."""

    entity_type: str = field(default="MatchSchedule", init=False)
    tournament_id: Optional[int] = None
    changed_fields: List[str] = field(default_factory=list)


@dataclass(frozen=True)
class MatchDeletedEvent(EntityEvent):
    """Emitted when a match is deleted."""

    entity_type: str = field(default="MatchSchedule", init=False)
    tournament_id: Optional[int] = None


@dataclass(frozen=True)
class MatchCompletedEvent(EntityEvent):
    """Emitted when a match is completed."""

    entity_type: str = field(default="MatchSchedule", init=False)
    tournament_id: Optional[int] = None
    winner_user_id: Optional[int] = None


@dataclass(frozen=True)
class MatchFinishedEvent(EntityEvent):
    """Emitted when a match race finishes and results are recorded."""

    entity_type: str = field(default="MatchSchedule", init=False)
    match_id: Optional[int] = None
    tournament_id: Optional[int] = None
    finisher_count: int = 0


@dataclass(frozen=True)
class TournamentMatchSettingsSubmittedEvent(EntityEvent):
    """Emitted when settings are submitted for a tournament match."""

    entity_type: str = field(default="TournamentMatchSettings", init=False)
    match_id: Optional[int] = None
    tournament_id: Optional[int] = None
    game_number: int = 1
    submitted_by_user_id: Optional[int] = None
    settings_data: Optional[dict] = None
    priority: EventPriority = EventPriority.NORMAL


# ============================================================================
# Crew Events
# ============================================================================


@dataclass(frozen=True)
class CrewAddedEvent(EntityEvent):
    """Emitted when crew is added to a match."""

    entity_type: str = field(default="Crew", init=False)
    match_id: Optional[int] = None
    crew_user_id: Optional[int] = None
    role: Optional[str] = None
    added_by_admin: bool = False
    auto_approved: bool = False


@dataclass(frozen=True)
class CrewApprovedEvent(EntityEvent):
    """Emitted when crew signup is approved."""

    entity_type: str = field(default="Crew", init=False)
    match_id: Optional[int] = None
    crew_user_id: Optional[int] = None
    role: Optional[str] = None
    approved_by_user_id: Optional[int] = None


@dataclass(frozen=True)
class CrewUnapprovedEvent(EntityEvent):
    """Emitted when crew approval is removed."""

    entity_type: str = field(default="Crew", init=False)
    match_id: Optional[int] = None
    crew_user_id: Optional[int] = None
    role: Optional[str] = None


@dataclass(frozen=True)
class CrewRemovedEvent(EntityEvent):
    """Emitted when crew is removed from a match."""

    entity_type: str = field(default="Crew", init=False)
    match_id: Optional[int] = None
    crew_user_id: Optional[int] = None
    role: Optional[str] = None


# ============================================================================
# Stream Channel Events
# ============================================================================


@dataclass(frozen=True)
class MatchChannelAssignedEvent(EntityEvent):
    """Emitted when a stream channel is assigned to a match."""

    entity_type: str = field(default="Match", init=False)
    match_id: Optional[int] = None
    stream_channel_id: Optional[int] = None
    stream_channel_name: Optional[str] = None


@dataclass(frozen=True)
class MatchChannelUnassignedEvent(EntityEvent):
    """Emitted when a stream channel is removed from a match."""

    entity_type: str = field(default="Match", init=False)
    match_id: Optional[int] = None
    previous_stream_channel_id: Optional[int] = None


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
    "CrewUnapprovedEvent",
    "CrewRemovedEvent",
    # Stream channel events
    "MatchChannelAssignedEvent",
    "MatchChannelUnassignedEvent",
]
