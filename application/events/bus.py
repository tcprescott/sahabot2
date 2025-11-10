"""
Event bus for publishing and subscribing to domain events.

The event bus is a singleton that manages event listeners and dispatches
events to registered handlers. It supports:
- Type-safe event registration
- Priority-based event processing
- Asynchronous event handling
- Error isolation (one handler failure doesn't affect others)
"""

import asyncio
import logging
from typing import Dict, List, Callable, Awaitable, Type, TypeVar, Optional
from collections import defaultdict

from application.events.base import BaseEvent, EventPriority

logger = logging.getLogger(__name__)

# Type variable for event types
TEvent = TypeVar("TEvent", bound=BaseEvent)

# Type alias for event handlers
EventHandler = Callable[[TEvent], Awaitable[None]]


class EventBus:
    """
    Singleton event bus for application-wide event handling.

    The event bus maintains a registry of event handlers and dispatches
    events to all registered listeners. Handlers are called asynchronously
    and errors in one handler do not affect others.

    Usage:
        # Register a handler
        @EventBus.on(UserCreatedEvent)
        async def on_user_created(event: UserCreatedEvent):
            logger.info("User %s created", event.user_id)

        # Emit an event
        event = UserCreatedEvent(user_id=123, organization_id=1)
        await EventBus.emit(event)
    """

    # Registry of handlers: event_type -> list of (priority, handler)
    _handlers: Dict[Type[BaseEvent], List[tuple[EventPriority, EventHandler]]] = (
        defaultdict(list)
    )

    # Lock for thread-safe handler registration
    _registration_lock = asyncio.Lock()

    # Toggle for enabling/disabling event processing (useful for testing)
    _enabled: bool = True

    @classmethod
    def enable(cls) -> None:
        """Enable event processing."""
        cls._enabled = True
        logger.info("Event bus enabled")

    @classmethod
    def disable(cls) -> None:
        """Disable event processing (events will be ignored)."""
        cls._enabled = False
        logger.warning("Event bus disabled - events will not be processed")

    @classmethod
    def is_enabled(cls) -> bool:
        """Check if event processing is enabled."""
        return cls._enabled

    @classmethod
    async def emit(cls, event: BaseEvent) -> None:
        """
        Emit an event to all registered handlers.

        Handlers are called asynchronously in priority order. If a handler
        raises an exception, it is logged but does not prevent other handlers
        from running.

        Args:
            event: The event to emit
        """
        if not cls._enabled:
            logger.debug("Event bus disabled, ignoring event: %s", event)
            return

        event_type = type(event)
        handlers = cls._handlers.get(event_type, [])

        if not handlers:
            logger.debug("No handlers registered for event: %s", event.event_type)
            return

        # Sort handlers by priority (highest first)
        sorted_handlers = sorted(handlers, key=lambda x: x[0], reverse=True)

        logger.debug(
            "Emitting event %s to %d handler(s)", event.event_type, len(sorted_handlers)
        )

        # Call handlers asynchronously
        tasks = []
        for priority, handler in sorted_handlers:
            task = asyncio.create_task(cls._call_handler(handler, event, priority))
            tasks.append(task)

        # Wait for all handlers to complete
        await asyncio.gather(*tasks, return_exceptions=True)

    @classmethod
    async def _call_handler(
        cls, handler: EventHandler, event: BaseEvent, priority: EventPriority
    ) -> None:
        """
        Call a single event handler with error handling.

        Args:
            handler: The handler function to call
            event: The event to pass to the handler
            priority: The handler's priority
        """
        try:
            await handler(event)
            logger.debug(
                "Handler %s completed for event %s (priority=%s)",
                handler.__name__,
                event.event_type,
                priority.name,
            )
        except Exception:
            logger.exception(
                "Error in event handler %s for event %s",
                handler.__name__,
                event.event_type,
            )

    @classmethod
    def on(
        cls, event_type: Type[TEvent], priority: EventPriority = EventPriority.NORMAL
    ) -> Callable[[EventHandler], EventHandler]:
        """
        Decorator to register an event handler.

        Args:
            event_type: The event class to listen for
            priority: Processing priority for this handler

        Returns:
            Decorator function

        Example:
            @EventBus.on(UserCreatedEvent, priority=EventPriority.HIGH)
            async def send_welcome_email(event: UserCreatedEvent):
                # Send email...
                pass
        """

        def decorator(handler: EventHandler) -> EventHandler:
            cls.register(event_type, handler, priority)
            return handler

        return decorator

    @classmethod
    def register(
        cls,
        event_type: Type[BaseEvent],
        handler: EventHandler,
        priority: EventPriority = EventPriority.NORMAL,
    ) -> None:
        """
        Register an event handler programmatically.

        Args:
            event_type: The event class to listen for
            handler: The async function to call when event is emitted
            priority: Processing priority for this handler
        """
        cls._handlers[event_type].append((priority, handler))
        logger.info(
            "Registered handler %s for event %s (priority=%s)",
            handler.__name__,
            event_type.__name__,
            priority.name,
        )

    @classmethod
    def unregister(
        cls, event_type: Type[BaseEvent], handler: Optional[EventHandler] = None
    ) -> None:
        """
        Unregister event handler(s).

        Args:
            event_type: The event class to unregister from
            handler: Specific handler to remove, or None to remove all handlers
        """
        if handler is None:
            # Remove all handlers for this event type
            if event_type in cls._handlers:
                count = len(cls._handlers[event_type])
                del cls._handlers[event_type]
                logger.info(
                    "Unregistered all %d handler(s) for event %s",
                    count,
                    event_type.__name__,
                )
        else:
            # Remove specific handler
            if event_type in cls._handlers:
                cls._handlers[event_type] = [
                    (p, h) for p, h in cls._handlers[event_type] if h != handler
                ]
                logger.info(
                    "Unregistered handler %s for event %s",
                    handler.__name__,
                    event_type.__name__,
                )

    @classmethod
    def clear_all(cls) -> None:
        """Clear all registered handlers. Useful for testing."""
        cls._handlers.clear()
        logger.warning("Cleared all event handlers")

    @classmethod
    def get_handler_count(cls, event_type: Optional[Type[BaseEvent]] = None) -> int:
        """
        Get count of registered handlers.

        Args:
            event_type: Specific event type, or None for total count

        Returns:
            Number of registered handlers
        """
        if event_type is None:
            return sum(len(handlers) for handlers in cls._handlers.values())
        return len(cls._handlers.get(event_type, []))
