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
"""

from application.events.bus import EventBus
from application.events.base import BaseEvent, EventPriority
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
    # Tournament events
    TournamentCreatedEvent,
    TournamentUpdatedEvent,
    TournamentDeletedEvent,
    TournamentStartedEvent,
    TournamentEndedEvent,
    # Match/Race events
    RaceSubmittedEvent,
    RaceApprovedEvent,
    RaceRejectedEvent,
    MatchScheduledEvent,
    MatchUpdatedEvent,
    MatchDeletedEvent,
    MatchCompletedEvent,
    MatchFinishedEvent,
    TournamentMatchSettingsSubmittedEvent,
    # Async Live Race events
    AsyncLiveRaceCreatedEvent,
    AsyncLiveRaceUpdatedEvent,
    AsyncLiveRaceRoomOpenedEvent,
    AsyncLiveRaceStartedEvent,
    AsyncLiveRaceFinishedEvent,
    AsyncLiveRaceCancelledEvent,
    # Crew events
    CrewAddedEvent,
    CrewApprovedEvent,
    CrewUnapprovedEvent,
    CrewRemovedEvent,
    # Stream Channel events
    MatchChannelAssignedEvent,
    MatchChannelUnassignedEvent,
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
)

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
    # Tournament events
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
]
