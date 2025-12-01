"""
SpeedGaming Plugin events.

This module exports SpeedGaming-related event types.
"""

from plugins.builtin.speedgaming.events.types import (
    SpeedGamingSyncStartedEvent,
    SpeedGamingSyncCompletedEvent,
)

__all__ = [
    "SpeedGamingSyncStartedEvent",
    "SpeedGamingSyncCompletedEvent",
]
