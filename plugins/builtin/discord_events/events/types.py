"""
DiscordEvents Plugin event types.

This module defines event types for Discord Scheduled Event operations.
"""

from dataclasses import dataclass
from typing import Optional

from application.events.base import BaseEvent


@dataclass(frozen=True)
class DiscordEventCreatedEvent(BaseEvent):
    """Emitted when a Discord scheduled event is created."""

    scheduled_event_id: int = 0
    match_id: int = 0
    event_slug: Optional[str] = None
    guild_id: int = 0

    @property
    def event_type(self) -> str:
        return "discord.scheduled_event.created"


@dataclass(frozen=True)
class DiscordEventUpdatedEvent(BaseEvent):
    """Emitted when a Discord scheduled event is updated."""

    scheduled_event_id: int = 0
    match_id: int = 0
    old_status: Optional[str] = None
    new_status: Optional[str] = None

    @property
    def event_type(self) -> str:
        return "discord.scheduled_event.updated"


@dataclass(frozen=True)
class DiscordEventDeletedEvent(BaseEvent):
    """Emitted when a Discord scheduled event is deleted."""

    scheduled_event_id: int = 0
    match_id: Optional[int] = None
    reason: str = ""  # e.g., "orphaned", "match_deleted", "manual"

    @property
    def event_type(self) -> str:
        return "discord.scheduled_event.deleted"
