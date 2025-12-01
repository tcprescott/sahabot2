"""
Event type definitions for the Presets plugin.

This module contains event classes for preset and namespace operations.
"""

from dataclasses import dataclass, field
from typing import Optional, List
from application.events.base import EntityEvent

# Re-export existing events from core
from application.events.types import (
    PresetCreatedEvent,
    PresetUpdatedEvent,
)


# ============================================================================
# Preset Events (additional types not in core)
# ============================================================================


@dataclass(frozen=True)
class PresetDeletedEvent(EntityEvent):
    """Emitted when a randomizer preset is deleted."""

    entity_type: str = field(default="RandomizerPreset", init=False)
    preset_name: Optional[str] = None
    namespace: Optional[str] = None


# ============================================================================
# Namespace Events
# ============================================================================


@dataclass(frozen=True)
class NamespaceCreatedEvent(EntityEvent):
    """Emitted when a preset namespace is created."""

    entity_type: str = field(default="PresetNamespace", init=False)
    namespace_name: Optional[str] = None
    owner_type: Optional[str] = None  # "user" or "organization"


@dataclass(frozen=True)
class NamespaceUpdatedEvent(EntityEvent):
    """Emitted when a preset namespace is updated."""

    entity_type: str = field(default="PresetNamespace", init=False)
    namespace_name: Optional[str] = None
    changed_fields: List[str] = field(default_factory=list)


__all__ = [
    "PresetCreatedEvent",
    "PresetUpdatedEvent",
    "PresetDeletedEvent",
    "NamespaceCreatedEvent",
    "NamespaceUpdatedEvent",
]
