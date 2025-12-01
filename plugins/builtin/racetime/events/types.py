"""
RaceTime Plugin event types.

This module defines event types for RaceTime-related operations.
"""

from dataclasses import dataclass
from typing import Optional

from application.events.base import BaseEvent


@dataclass(frozen=True)
class RaceRoomCreatedEvent(BaseEvent):
    """Emitted when a RaceTime room is created or joined."""

    room_slug: str = ""
    category: str = ""
    match_id: Optional[int] = None
    bot_id: Optional[int] = None

    @property
    def event_type(self) -> str:
        return "racetime.room.created"


@dataclass(frozen=True)
class RaceRoomFinishedEvent(BaseEvent):
    """Emitted when a RaceTime room race finishes."""

    room_slug: str = ""
    category: str = ""
    match_id: Optional[int] = None
    finish_status: str = ""  # finished, cancelled

    @property
    def event_type(self) -> str:
        return "racetime.room.finished"


@dataclass(frozen=True)
class RacetimeBotStatusChangedEvent(BaseEvent):
    """Emitted when a RaceTime bot's status changes."""

    bot_id: int = 0
    category: str = ""
    old_status: int = 0
    new_status: int = 0
    status_message: Optional[str] = None

    @property
    def event_type(self) -> str:
        return "racetime.bot.status_changed"
