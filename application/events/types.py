"""
Domain event type definitions.

This module contains concrete event classes for all major domain operations.
Events are organized by domain area (users, organizations, tournaments, etc.)
and follow consistent naming patterns:
- {Entity}CreatedEvent - When an entity is created
- {Entity}UpdatedEvent - When an entity is modified
- {Entity}DeletedEvent - When an entity is removed
- {Entity}{Action}Event - For specific domain actions
"""

from dataclasses import dataclass, field
from typing import Optional, List
from application.events.base import EntityEvent, EventPriority


# ============================================================================
# User Events
# ============================================================================

@dataclass(frozen=True)
class UserCreatedEvent(EntityEvent):
    """Emitted when a new user is created."""
    entity_type: str = field(default="User", init=False)
    discord_id: Optional[int] = None
    discord_username: Optional[str] = None


@dataclass(frozen=True)
class UserUpdatedEvent(EntityEvent):
    """Emitted when a user's information is updated."""
    entity_type: str = field(default="User", init=False)
    changed_fields: List[str] = field(default_factory=list)


@dataclass(frozen=True)
class UserDeletedEvent(EntityEvent):
    """Emitted when a user is deleted or deactivated."""
    entity_type: str = field(default="User", init=False)
    reason: Optional[str] = None


@dataclass(frozen=True)
class UserPermissionChangedEvent(EntityEvent):
    """Emitted when a user's global permission level changes."""
    entity_type: str = field(default="User", init=False)
    old_permission: Optional[str] = None
    new_permission: Optional[str] = None


# ============================================================================
# Organization Events
# ============================================================================

@dataclass(frozen=True)
class OrganizationCreatedEvent(EntityEvent):
    """Emitted when a new organization is created."""
    entity_type: str = field(default="Organization", init=False)
    organization_name: Optional[str] = None


@dataclass(frozen=True)
class OrganizationUpdatedEvent(EntityEvent):
    """Emitted when an organization is updated."""
    entity_type: str = field(default="Organization", init=False)
    changed_fields: List[str] = field(default_factory=list)


@dataclass(frozen=True)
class OrganizationDeletedEvent(EntityEvent):
    """Emitted when an organization is deleted or deactivated."""
    entity_type: str = field(default="Organization", init=False)
    reason: Optional[str] = None


@dataclass(frozen=True)
class OrganizationMemberAddedEvent(EntityEvent):
    """Emitted when a user is added to an organization."""
    entity_type: str = field(default="OrganizationMember", init=False)
    member_user_id: Optional[int] = None
    added_by_user_id: Optional[int] = None


@dataclass(frozen=True)
class OrganizationMemberRemovedEvent(EntityEvent):
    """Emitted when a user is removed from an organization."""
    entity_type: str = field(default="OrganizationMember", init=False)
    member_user_id: Optional[int] = None
    removed_by_user_id: Optional[int] = None
    reason: Optional[str] = None


@dataclass(frozen=True)
class OrganizationMemberPermissionChangedEvent(EntityEvent):
    """Emitted when a member's permissions within an org change."""
    entity_type: str = field(default="OrganizationMember", init=False)
    member_user_id: Optional[int] = None
    permission_name: Optional[str] = None
    granted: bool = False  # True if permission granted, False if revoked


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
# Match/Race Events
# ============================================================================

@dataclass(frozen=True)
class RaceSubmittedEvent(EntityEvent):
    """Emitted when a player submits a race result."""
    entity_type: str = field(default="AsyncTournamentRace", init=False)
    tournament_id: Optional[int] = None
    permalink_id: Optional[int] = None
    racer_user_id: Optional[int] = None
    time_seconds: Optional[int] = None
    vod_url: Optional[str] = None


@dataclass(frozen=True)
class RaceApprovedEvent(EntityEvent):
    """Emitted when a race submission is approved by a reviewer."""
    entity_type: str = field(default="AsyncTournamentRace", init=False)
    tournament_id: Optional[int] = None
    racer_user_id: Optional[int] = None
    reviewer_user_id: Optional[int] = None


@dataclass(frozen=True)
class RaceRejectedEvent(EntityEvent):
    """Emitted when a race submission is rejected by a reviewer."""
    entity_type: str = field(default="AsyncTournamentRace", init=False)
    tournament_id: Optional[int] = None
    racer_user_id: Optional[int] = None
    reviewer_user_id: Optional[int] = None
    reason: Optional[str] = None


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
# Async Live Race Events
# ============================================================================

@dataclass(frozen=True)
class AsyncLiveRaceCreatedEvent(EntityEvent):
    """Emitted when a new live race is scheduled."""
    entity_type: str = field(default="AsyncTournamentLiveRace", init=False)
    tournament_id: Optional[int] = None
    pool_id: Optional[int] = None
    scheduled_at: Optional[str] = None  # ISO format
    match_title: Optional[str] = None


@dataclass(frozen=True)
class AsyncLiveRaceUpdatedEvent(EntityEvent):
    """Emitted when a live race is updated."""
    entity_type: str = field(default="AsyncTournamentLiveRace", init=False)
    tournament_id: Optional[int] = None
    changed_fields: List[str] = field(default_factory=list)


@dataclass(frozen=True)
class AsyncLiveRaceRoomOpenedEvent(EntityEvent):
    """Emitted when a RaceTime.gg room is opened for a live race."""
    entity_type: str = field(default="AsyncTournamentLiveRace", init=False)
    tournament_id: Optional[int] = None
    racetime_slug: Optional[str] = None
    racetime_url: Optional[str] = None
    scheduled_at: Optional[str] = None  # ISO format
    priority: EventPriority = EventPriority.HIGH


@dataclass(frozen=True)
class AsyncLiveRaceStartedEvent(EntityEvent):
    """Emitted when a live race countdown completes and race begins."""
    entity_type: str = field(default="AsyncTournamentLiveRace", init=False)
    tournament_id: Optional[int] = None
    racetime_slug: Optional[str] = None
    participant_count: int = 0
    priority: EventPriority = EventPriority.HIGH


@dataclass(frozen=True)
class AsyncLiveRaceFinishedEvent(EntityEvent):
    """Emitted when a live race completes and results are recorded."""
    entity_type: str = field(default="AsyncTournamentLiveRace", init=False)
    tournament_id: Optional[int] = None
    racetime_slug: Optional[str] = None
    finisher_count: int = 0
    priority: EventPriority = EventPriority.HIGH


@dataclass(frozen=True)
class AsyncLiveRaceCancelledEvent(EntityEvent):
    """Emitted when a live race is cancelled."""
    entity_type: str = field(default="AsyncTournamentLiveRace", init=False)
    tournament_id: Optional[int] = None
    reason: Optional[str] = None
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


# ============================================================================
# Invite Events
# ============================================================================

@dataclass(frozen=True)
class InviteCreatedEvent(EntityEvent):
    """Emitted when an organization invite is created."""
    entity_type: str = field(default="OrganizationInvite", init=False)
    invite_code: Optional[str] = None
    inviter_user_id: Optional[int] = None
    invited_email: Optional[str] = None


@dataclass(frozen=True)
class InviteAcceptedEvent(EntityEvent):
    """Emitted when an invite is accepted."""
    entity_type: str = field(default="OrganizationInvite", init=False)
    invite_code: Optional[str] = None
    accepted_by_user_id: Optional[int] = None


@dataclass(frozen=True)
class InviteRejectedEvent(EntityEvent):
    """Emitted when an invite is rejected."""
    entity_type: str = field(default="OrganizationInvite", init=False)
    invite_code: Optional[str] = None
    rejected_by_user_id: Optional[int] = None


@dataclass(frozen=True)
class InviteExpiredEvent(EntityEvent):
    """Emitted when an invite expires."""
    entity_type: str = field(default="OrganizationInvite", init=False)
    invite_code: Optional[str] = None
    priority: EventPriority = EventPriority.LOW


# ============================================================================
# Additional Event Types (for future expansion)
# ============================================================================

@dataclass(frozen=True)
class DiscordGuildLinkedEvent(EntityEvent):
    """Emitted when a Discord guild is linked to an organization."""
    entity_type: str = field(default="DiscordGuild", init=False)
    guild_id: Optional[str] = None
    guild_name: Optional[str] = None


@dataclass(frozen=True)
class DiscordGuildUnlinkedEvent(EntityEvent):
    """Emitted when a Discord guild is unlinked from an organization."""
    entity_type: str = field(default="DiscordGuild", init=False)
    guild_id: Optional[str] = None
    reason: Optional[str] = None


@dataclass(frozen=True)
class PresetCreatedEvent(EntityEvent):
    """Emitted when a randomizer preset is created."""
    entity_type: str = field(default="RandomizerPreset", init=False)
    preset_name: Optional[str] = None
    namespace: Optional[str] = None


@dataclass(frozen=True)
class PresetUpdatedEvent(EntityEvent):
    """Emitted when a randomizer preset is updated."""
    entity_type: str = field(default="RandomizerPreset", init=False)
    preset_name: Optional[str] = None
    changed_fields: List[str] = field(default_factory=list)


# ============================================================================
# RaceTime Bot Events
# ============================================================================

@dataclass(frozen=True)
class RacetimeBotCreatedEvent(EntityEvent):
    """Emitted when a RaceTime bot is created."""
    entity_type: str = field(default="RacetimeBot", init=False)
    category: Optional[str] = None
    name: Optional[str] = None


@dataclass(frozen=True)
class RacetimeBotUpdatedEvent(EntityEvent):
    """Emitted when a RaceTime bot is updated."""
    entity_type: str = field(default="RacetimeBot", init=False)
    category: Optional[str] = None
    changed_fields: List[str] = field(default_factory=list)


@dataclass(frozen=True)
class RacetimeBotDeletedEvent(EntityEvent):
    """Emitted when a RaceTime bot is deleted."""
    entity_type: str = field(default="RacetimeBot", init=False)
    category: Optional[str] = None


# ============================================================================
# RaceTime Room Events
# ============================================================================

@dataclass(frozen=True)
class RacetimeRoomCreatedEvent(EntityEvent):
    """Emitted when a RaceTime.gg race room is created for a match."""
    entity_type: str = field(default="Match", init=False)
    match_id: Optional[int] = None
    tournament_id: Optional[int] = None
    room_slug: Optional[str] = None  # e.g., "alttpr/cool-doge-1234"
    goal: Optional[str] = None
    player_count: int = 0
    invited_count: int = 0
    priority: EventPriority = EventPriority.HIGH


@dataclass(frozen=True)
class RacetimeRoomOpenedEvent(EntityEvent):
    """Emitted when a RaceTime.gg race room is manually opened."""
    entity_type: str = field(default="Match", init=False)
    match_id: Optional[int] = None
    tournament_id: Optional[int] = None
    room_slug: Optional[str] = None
    opened_by_user_id: Optional[int] = None


@dataclass(frozen=True)
class RacetimeRaceStatusChangedEvent(EntityEvent):
    """
    Emitted when a RaceTime.gg race changes status.

    Status values from racetime.gg:
    - open: Race room is open for entrants to join
    - invitational: Race room is invite-only
    - pending: Race countdown has started
    - in_progress: Race is currently running
    - finished: Race has completed
    - cancelled: Race was cancelled
    """
    entity_type: str = field(default="RacetimeRace", init=False)
    category: str = ""  # e.g., "alttpr"
    room_slug: str = ""  # e.g., "alttpr/cool-doge-1234"
    room_name: str = ""  # e.g., "cool-doge-1234"
    old_status: Optional[str] = None  # Previous status value
    new_status: str = ""  # Current status value
    match_id: Optional[int] = None  # Associated match ID if any
    tournament_id: Optional[int] = None  # Associated tournament ID if any
    entrant_count: int = 0  # Number of entrants in race
    started_at: Optional[str] = None  # ISO 8601 datetime when race started (if in_progress or finished)
    ended_at: Optional[str] = None  # ISO 8601 datetime when race ended (if finished or cancelled)
    priority: EventPriority = EventPriority.HIGH


@dataclass(frozen=True)
class RacetimeEntrantStatusChangedEvent(EntityEvent):
    """
    Emitted when a racer's status changes in a RaceTime.gg race.

    Tracks status changes like joining, readying up, starting, finishing, forfeiting, etc.

    Entrant status values from racetime.gg:
    - requested: User has requested to join (invitational races only)
    - invited: User has been invited but not yet joined
    - not_ready: User has joined but not marked ready
    - ready: User is ready to race
    - in_progress: User is currently racing
    - done: User has finished the race
    - dnf: User did not finish (forfeited)
    - dq: User was disqualified
    """
    entity_type: str = field(default="RacetimeEntrant", init=False)
    category: str = ""  # e.g., "alttpr"
    room_slug: str = ""  # e.g., "alttpr/cool-doge-1234"
    room_name: str = ""  # e.g., "cool-doge-1234"
    racetime_user_id: str = ""  # Racetime.gg user hash ID
    racetime_user_name: str = ""  # Racetime.gg user name
    user_id: Optional[int] = None  # Application user ID (None if racetime account not linked)
    old_status: Optional[str] = None  # Previous status value
    new_status: str = ""  # Current status value
    finish_time: Optional[str] = None  # ISO 8601 duration (e.g., "PT1H23M45S") if done
    place: Optional[int] = None  # Placement if finished (1, 2, 3, etc.)
    match_id: Optional[int] = None  # Associated match ID if any
    tournament_id: Optional[int] = None  # Associated tournament ID if any
    race_status: str = ""  # Current overall race status
    priority: EventPriority = EventPriority.NORMAL


@dataclass(frozen=True)
class RacetimeEntrantJoinedEvent(EntityEvent):
    """
    Emitted when a player joins a RaceTime.gg race room.
    
    This event fires when a new entrant first appears in the race,
    regardless of their initial status (requested, invited, not_ready, etc.).
    """
    entity_type: str = field(default="RacetimeEntrant", init=False)
    category: str = ""  # e.g., "alttpr"
    room_slug: str = ""  # e.g., "alttpr/cool-doge-1234"
    room_name: str = ""  # e.g., "cool-doge-1234"
    racetime_user_id: str = ""  # Racetime.gg user hash ID
    racetime_user_name: str = ""  # Racetime.gg user name
    user_id: Optional[int] = None  # Application user ID (None if racetime account not linked)
    initial_status: str = ""  # Initial status when joining (usually "not_ready" or "requested")
    match_id: Optional[int] = None  # Associated match ID if any
    tournament_id: Optional[int] = None  # Associated tournament ID if any
    race_status: str = ""  # Current overall race status
    priority: EventPriority = EventPriority.NORMAL


@dataclass(frozen=True)
class RacetimeEntrantLeftEvent(EntityEvent):
    """
    Emitted when a player leaves a RaceTime.gg race room.
    
    This event fires when an entrant is removed from the race
    (either voluntarily or by race monitors).
    """
    entity_type: str = field(default="RacetimeEntrant", init=False)
    category: str = ""  # e.g., "alttpr"
    room_slug: str = ""  # e.g., "alttpr/cool-doge-1234"
    room_name: str = ""  # e.g., "cool-doge-1234"
    racetime_user_id: str = ""  # Racetime.gg user hash ID
    racetime_user_name: str = ""  # Racetime.gg user name
    user_id: Optional[int] = None  # Application user ID (None if racetime account not linked)
    last_status: str = ""  # Status when they left
    match_id: Optional[int] = None  # Associated match ID if any
    tournament_id: Optional[int] = None  # Associated tournament ID if any
    race_status: str = ""  # Current overall race status
    priority: EventPriority = EventPriority.NORMAL


@dataclass(frozen=True)
class RacetimeEntrantInvitedEvent(EntityEvent):
    """
    Emitted when a player is invited to a RaceTime.gg race room.
    
    This event fires when the bot invites a user to the race.
    Note: This only fires for invitations sent by this bot instance,
    not for invitations sent via the web UI or by other bots.
    """
    entity_type: str = field(default="RacetimeEntrant", init=False)
    category: str = ""  # e.g., "alttpr"
    room_slug: str = ""  # e.g., "alttpr/cool-doge-1234"
    room_name: str = ""  # e.g., "cool-doge-1234"
    racetime_user_id: str = ""  # Racetime.gg user hash ID being invited
    racetime_user_name: Optional[str] = None  # Racetime.gg user name (if available)
    user_id: Optional[int] = None  # Application user ID (None if racetime account not linked)
    match_id: Optional[int] = None  # Associated match ID if any
    tournament_id: Optional[int] = None  # Associated tournament ID if any
    race_status: str = ""  # Current overall race status
    priority: EventPriority = EventPriority.NORMAL


@dataclass(frozen=True)
class RacetimeBotJoinedRaceEvent(EntityEvent):
    """
    Emitted when the bot joins an existing RaceTime.gg race room.
    
    This event fires when the bot's handler is created for a race
    it is joining (not creating).
    """
    entity_type: str = field(default="RacetimeRace", init=False)
    category: str = ""  # e.g., "alttpr"
    room_slug: str = ""  # e.g., "alttpr/cool-doge-1234"
    room_name: str = ""  # e.g., "cool-doge-1234"
    race_status: str = ""  # Current race status when bot joined
    entrant_count: int = 0  # Number of entrants when bot joined
    match_id: Optional[int] = None  # Associated match ID if any
    tournament_id: Optional[int] = None  # Associated tournament ID if any
    bot_action: str = "join"  # Always "join" for this event
    priority: EventPriority = EventPriority.HIGH


@dataclass(frozen=True)
class RacetimeBotCreatedRaceEvent(EntityEvent):
    """
    Emitted when the bot creates/opens a new RaceTime.gg race room.
    
    This event fires when the bot successfully creates a new race room
    (via startrace or equivalent).
    """
    entity_type: str = field(default="RacetimeRace", init=False)
    category: str = ""  # e.g., "alttpr"
    room_slug: str = ""  # e.g., "alttpr/cool-doge-1234"
    room_name: str = ""  # e.g., "cool-doge-1234"
    goal: str = ""  # Race goal text
    invitational: bool = False  # Whether race is invite-only
    match_id: Optional[int] = None  # Associated match ID if any
    tournament_id: Optional[int] = None  # Associated tournament ID if any
    bot_action: str = "create"  # Always "create" for this event
    priority: EventPriority = EventPriority.HIGH


@dataclass(frozen=True)
class RacetimeBotActionEvent(EntityEvent):
    """
    Emitted when the bot performs an action on a RaceTime.gg race room.
    
    This is a generic event for bot actions like force_start, cancel_race,
    pin_message, set_raceinfo, etc.
    """
    entity_type: str = field(default="RacetimeRace", init=False)
    category: str = ""  # e.g., "alttpr"
    room_slug: str = ""  # e.g., "alttpr/cool-doge-1234"
    room_name: str = ""  # e.g., "cool-doge-1234"
    action_type: str = ""  # Action performed (e.g., "force_start", "cancel_race")
    target_user_id: Optional[str] = None  # Target racetime user ID (for user-specific actions)
    details: Optional[str] = None  # Additional action details
    priority: EventPriority = EventPriority.NORMAL


# ============================================================================
# Scheduled Task Events
# ============================================================================

@dataclass(frozen=True)
class BuiltinTaskOverrideUpdatedEvent(EntityEvent):
    """Emitted when a builtin task's override is created or updated."""
    entity_type: str = field(default="BuiltinTaskOverride", init=False)
    task_id: str = ""
    is_active: bool = False
    previous_is_active: Optional[bool] = None  # None if newly created

