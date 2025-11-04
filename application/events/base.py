"""
Base event classes for the event system.

This module defines the foundational classes that all domain events inherit from.
Events are immutable data structures that represent something that happened in the system.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional, Any, Dict
from enum import IntEnum
import uuid


class EventPriority(IntEnum):
    """Priority levels for event processing.

    Higher priority events are processed before lower priority events.
    Use CRITICAL for events that must be processed immediately (e.g., security events).
    Use HIGH for important operational events (e.g., user actions).
    Use NORMAL for standard domain events (e.g., data changes).
    Use LOW for background/analytics events.
    """
    CRITICAL = 100
    HIGH = 75
    NORMAL = 50
    LOW = 25


@dataclass(frozen=True)
class BaseEvent:
    """
    Base class for all domain events.

    Events are immutable records of something that happened in the system.
    They should contain all necessary context for event handlers to operate
    independently without needing to query the database.

    Attributes:
        event_id: Unique identifier for this event instance
        timestamp: When the event occurred (UTC)
        user_id: ID of the user who triggered the event (if applicable)
        organization_id: ID of the organization context (if applicable)
        priority: Processing priority for this event
        metadata: Additional context-specific data
    """

    # Core event metadata (auto-generated)
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    # Common context fields (set by event creators)
    user_id: Optional[int] = None
    organization_id: Optional[int] = None

    # Processing metadata
    priority: EventPriority = EventPriority.NORMAL
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def event_type(self) -> str:
        """Return the event type name (class name)."""
        return self.__class__.__name__

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert event to dictionary representation.

        Useful for serialization, logging, and storage.
        """
        return {
            "event_id": self.event_id,
            "event_type": self.event_type,
            "timestamp": self.timestamp.isoformat(),
            "user_id": self.user_id,
            "organization_id": self.organization_id,
            "priority": self.priority.value,
            "metadata": self.metadata,
        }

    def __str__(self) -> str:
        """Return human-readable event representation."""
        return f"{self.event_type}(id={self.event_id[:8]}, user={self.user_id}, org={self.organization_id})"


@dataclass(frozen=True)
class EntityEvent(BaseEvent):
    """
    Base class for events related to entity lifecycle (create, update, delete).

    Attributes:
        entity_type: Type of entity (e.g., "User", "Tournament")
        entity_id: ID of the entity affected
        entity_data: Snapshot of relevant entity data at event time
    """
    entity_type: str = ""
    entity_id: Optional[int] = None
    entity_data: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary with entity fields."""
        base = super().to_dict()
        base.update({
            "entity_type": self.entity_type,
            "entity_id": self.entity_id,
            "entity_data": self.entity_data,
        })
        return base
