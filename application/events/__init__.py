"""
Event system for SahaBot2.

This package provides an event-driven architecture for handling asynchronous
notifications and cross-cutting concerns like audit logging, notifications, etc.

The event system follows these principles:
- Events are emitted from the service layer after successful operations
- Events are handled asynchronously by registered listeners
- Events carry all necessary context for handlers to operate independently
- Events are typed and structured for type safety and clarity

Usage:
    from application.events import EventBus, UserCreatedEvent

    # In a service:
    event = UserCreatedEvent(user_id=user.id, organization_id=org.id)
    await EventBus.emit(event)

    # Register a listener:
    @EventBus.on(UserCreatedEvent)
    async def on_user_created(event: UserCreatedEvent):
        # Handle the event
        pass

Note: Tournament-related events are defined in plugins.builtin.tournament.events.
For backward compatibility, they are lazily re-exported here via __getattr__.
"""

from application.events.bus import EventBus
from application.events.base import BaseEvent, EventPriority

# Import non-tournament events from types.py
from application.events.types import (
    # User events
    UserCreatedEvent,
    UserUpdatedEvent,
    UserDeletedEvent,
    UserPermissionChangedEvent,
    # Organization events
    OrganizationCreatedEvent,
    OrganizationUpdatedEvent,
    OrganizationDeletedEvent,
    OrganizationMemberAddedEvent,
    OrganizationMemberRemovedEvent,
    OrganizationMemberPermissionChangedEvent,
    # Race events (async qualifiers)
    RaceSubmittedEvent,
    RaceApprovedEvent,
    RaceRejectedEvent,
    # Async Live Race events
    AsyncLiveRaceCreatedEvent,
    AsyncLiveRaceUpdatedEvent,
    AsyncLiveRaceRoomOpenedEvent,
    AsyncLiveRaceStartedEvent,
    AsyncLiveRaceFinishedEvent,
    AsyncLiveRaceCancelledEvent,
    # Invite events
    InviteCreatedEvent,
    InviteAcceptedEvent,
    InviteRejectedEvent,
    InviteExpiredEvent,
    # Discord events
    DiscordGuildLinkedEvent,
    DiscordGuildUnlinkedEvent,
    # Preset events
    PresetCreatedEvent,
    PresetUpdatedEvent,
    # RaceTime bot events
    RacetimeBotCreatedEvent,
    RacetimeBotUpdatedEvent,
    RacetimeBotDeletedEvent,
    # RaceTime room events
    RacetimeRoomCreatedEvent,
    RacetimeRoomOpenedEvent,
    # RaceTime race/entrant events
    RacetimeRaceStatusChangedEvent,
    RacetimeEntrantStatusChangedEvent,
    RacetimeEntrantJoinedEvent,
    RacetimeEntrantLeftEvent,
    RacetimeEntrantInvitedEvent,
    RacetimeBotJoinedRaceEvent,
    RacetimeBotCreatedRaceEvent,
    RacetimeBotActionEvent,
    # Scheduled Task events
    BuiltinTaskOverrideUpdatedEvent,
)

# Tournament events are now in the plugin.
# We use __getattr__ for lazy loading to avoid circular imports.
_TOURNAMENT_EVENTS = {
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
}


def __getattr__(name: str):
    """Lazy load tournament events from the plugin to avoid circular imports."""
    if name in _TOURNAMENT_EVENTS:
        from plugins.builtin.tournament.events import types as tournament_events

        return getattr(tournament_events, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = [
    # Core
    "EventBus",
    "BaseEvent",
    "EventPriority",
    # User events
    "UserCreatedEvent",
    "UserUpdatedEvent",
    "UserDeletedEvent",
    "UserPermissionChangedEvent",
    # Organization events
    "OrganizationCreatedEvent",
    "OrganizationUpdatedEvent",
    "OrganizationDeletedEvent",
    "OrganizationMemberAddedEvent",
    "OrganizationMemberRemovedEvent",
    "OrganizationMemberPermissionChangedEvent",
    # Tournament events (lazy loaded from plugin)
    "TournamentCreatedEvent",
    "TournamentUpdatedEvent",
    "TournamentDeletedEvent",
    "TournamentStartedEvent",
    "TournamentEndedEvent",
    # Match/Race events
    "RaceSubmittedEvent",
    "RaceApprovedEvent",
    "RaceRejectedEvent",
    "MatchScheduledEvent",
    "MatchUpdatedEvent",
    "MatchDeletedEvent",
    "MatchCompletedEvent",
    "MatchFinishedEvent",
    "TournamentMatchSettingsSubmittedEvent",
    # Async Live Race events
    "AsyncLiveRaceCreatedEvent",
    "AsyncLiveRaceUpdatedEvent",
    "AsyncLiveRaceRoomOpenedEvent",
    "AsyncLiveRaceStartedEvent",
    "AsyncLiveRaceFinishedEvent",
    "AsyncLiveRaceCancelledEvent",
    # Crew events
    "CrewAddedEvent",
    "CrewApprovedEvent",
    "CrewUnapprovedEvent",
    "CrewRemovedEvent",
    # Stream Channel events
    "MatchChannelAssignedEvent",
    "MatchChannelUnassignedEvent",
    # Invite events
    "InviteCreatedEvent",
    "InviteAcceptedEvent",
    "InviteRejectedEvent",
    "InviteExpiredEvent",
    # Discord events
    "DiscordGuildLinkedEvent",
    "DiscordGuildUnlinkedEvent",
    # Preset events
    "PresetCreatedEvent",
    "PresetUpdatedEvent",
    # RaceTime bot events
    "RacetimeBotCreatedEvent",
    "RacetimeBotUpdatedEvent",
    "RacetimeBotDeletedEvent",
    # RaceTime room events
    "RacetimeRoomCreatedEvent",
    "RacetimeRoomOpenedEvent",
    # RaceTime race/entrant events
    "RacetimeRaceStatusChangedEvent",
    "RacetimeEntrantStatusChangedEvent",
    "RacetimeEntrantJoinedEvent",
    "RacetimeEntrantLeftEvent",
    "RacetimeEntrantInvitedEvent",
    "RacetimeBotJoinedRaceEvent",
    "RacetimeBotCreatedRaceEvent",
    "RacetimeBotActionEvent",
    # Scheduled Task events
    "BuiltinTaskOverrideUpdatedEvent",
]
