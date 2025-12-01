"""
Event provider interface.

This module defines the interface for plugins that contribute events and listeners.
"""

from abc import ABC, abstractmethod
from typing import Callable, List, Type
from dataclasses import dataclass
from enum import IntEnum


class EventPriority(IntEnum):
    """Event listener priority levels."""

    LOWEST = 0
    LOW = 25
    NORMAL = 50
    HIGH = 75
    HIGHEST = 100


@dataclass
class EventListenerRegistration:
    """Event listener registration."""

    event_type: Type
    handler: Callable
    priority: EventPriority = EventPriority.NORMAL


class EventProvider(ABC):
    """Interface for plugins that provide events."""

    @abstractmethod
    def get_event_types(self) -> List[Type]:
        """
        Return event types defined by this plugin.

        Returns:
            List of BaseEvent subclasses
        """
        pass

    @abstractmethod
    def get_event_listeners(self) -> List[EventListenerRegistration]:
        """
        Return event listeners to register.

        Returns:
            List of EventListenerRegistration instances
        """
        pass

    def register_events(self) -> None:
        """
        Register events and listeners with EventBus.

        Called by PluginRegistry during event registration.
        """
        # Import here to avoid circular imports
        from application.events import EventBus

        for listener in self.get_event_listeners():
            EventBus.register(
                listener.event_type, listener.handler, listener.priority
            )
