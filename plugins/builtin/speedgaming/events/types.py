"""
SpeedGaming Plugin event types.

This module defines event types for SpeedGaming-related operations.
"""

from dataclasses import dataclass
from typing import Optional

from application.events.base import BaseEvent


@dataclass(frozen=True)
class SpeedGamingSyncStartedEvent(BaseEvent):
    """Emitted when a SpeedGaming sync starts."""

    tournament_id: Optional[int] = None  # None for all-tournament sync
    event_slug: Optional[str] = None

    @property
    def event_type(self) -> str:
        return "speedgaming.sync.started"


@dataclass(frozen=True)
class SpeedGamingSyncCompletedEvent(BaseEvent):
    """Emitted when a SpeedGaming sync completes."""

    tournament_id: Optional[int] = None  # None for all-tournament sync
    event_slug: Optional[str] = None
    imported_count: int = 0
    updated_count: int = 0
    deleted_count: int = 0
    success: bool = True
    error_message: Optional[str] = None

    @property
    def event_type(self) -> str:
        return "speedgaming.sync.completed"
