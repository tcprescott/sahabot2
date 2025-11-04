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
class MatchCompletedEvent(EntityEvent):
    """Emitted when a match is completed."""
    entity_type: str = field(default="MatchSchedule", init=False)
    tournament_id: Optional[int] = None
    winner_user_id: Optional[int] = None


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
