"""
Events for the Presets plugin.

This module exports preset-related events.
"""

from plugins.builtin.presets.events.types import (
    PresetCreatedEvent,
    PresetUpdatedEvent,
    PresetDeletedEvent,
    NamespaceCreatedEvent,
    NamespaceUpdatedEvent,
)

__all__ = [
    "PresetCreatedEvent",
    "PresetUpdatedEvent",
    "PresetDeletedEvent",
    "NamespaceCreatedEvent",
    "NamespaceUpdatedEvent",
]
