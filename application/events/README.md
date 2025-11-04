# Application Events Package

This package provides the event system for SahaBot2, enabling asynchronous event-driven architecture for notifications, audit logging, and other cross-cutting concerns.

## Quick Start

### Emitting Events from Services

```python
from application.events import EventBus, UserCreatedEvent

# After successful operation
user = await self.repository.create(...)

# Emit event
event = UserCreatedEvent(
    entity_id=user.id,
    user_id=acting_user_id,
    organization_id=org_id,
    discord_id=user.discord_id,
    discord_username=user.discord_username
)
await EventBus.emit(event)
```

### Listening to Events

```python
from application.events import EventBus, EventPriority, UserCreatedEvent

@EventBus.on(UserCreatedEvent, priority=EventPriority.HIGH)
async def on_user_created(event: UserCreatedEvent):
    logger.info("User %s created", event.entity_id)
    # Perform action...
```

## Package Structure

- `base.py` - Base event classes (`BaseEvent`, `EntityEvent`, `EventPriority`)
- `bus.py` - Event bus singleton for event emission and handler registration
- `types.py` - Concrete event type definitions for all domain operations
- `listeners.py` - Registered event handlers (auto-imported on app startup)
- `__init__.py` - Public API exports

## Documentation

See [EVENT_SYSTEM.md](../../docs/EVENT_SYSTEM.md) for comprehensive guide including:
- Architecture overview
- Event flow diagrams
- Complete event catalog
- Usage patterns and best practices
- Testing strategies
- Future expansion plans

## Testing

Run event system tests:
```bash
poetry run pytest tests/unit/test_event_system.py -v
```

Disable events in your tests:
```python
from application.events import EventBus

EventBus.disable()  # Events will be ignored
# ... run tests ...
EventBus.enable()   # Re-enable
```

## Current Features

✅ Type-safe event definitions
✅ Priority-based handler execution
✅ Async/await support
✅ Error isolation (handler failures don't affect others)
✅ Automatic audit logging for major events
✅ Enable/disable toggle for testing
✅ Handler registration/unregistration

## Roadmap

- [ ] Discord notification handlers
- [ ] Email notification system
- [ ] Webhook integrations
- [ ] Event persistence/replay
- [ ] Event streaming API
- [ ] In-app notification center

## Contributing

When adding new events:
1. Define event class in `types.py`
2. Export from `__init__.py`
3. Emit from service layer after successful operations
4. Add handler in `listeners.py` if needed
5. Update documentation

See [EVENT_SYSTEM.md](../../docs/EVENT_SYSTEM.md) for detailed guidelines.
