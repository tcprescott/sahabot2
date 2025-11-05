# Event System Guide

## Overview

The SahaBot2 event system provides a robust, type-safe mechanism for handling asynchronous notifications and cross-cutting concerns. Events are emitted from the service layer when significant domain operations occur, and they are processed by registered listeners in a fire-and-forget manner.

## Architecture

### Core Components

1. **BaseEvent & EntityEvent** (`application/events/base.py`)
   - Immutable dataclasses representing things that happened in the system
   - Automatically include event ID, timestamp, user context, organization context
   - EntityEvent adds entity-specific fields (type, ID, data snapshot)

2. **EventBus** (`application/events/bus.py`)
   - Singleton event dispatcher
   - Manages event listener registration and invocation
   - Supports priority-based processing
   - Isolates errors (one handler failure doesn't affect others)

3. **Event Types** (`application/events/types.py`)
   - Concrete event definitions for all major domain operations
   - Organized by domain (users, organizations, tournaments, etc.)
   - Follow consistent naming: `{Entity}{Action}Event`

4. **Event Listeners** (`application/events/listeners.py`)
   - Registered handlers that respond to events
   - Currently implements audit logging for major events
   - Placeholder structure for future notification handlers

## Event Flow

```
Service Layer                Event Bus                  Listeners
─────────────                ─────────                  ─────────
[Business Logic]             [EventBus]
      │                           │
      ├─ Perform operation        │
      │  (database write)          │
      │                           │
      └─ await EventBus.emit() ───┤
                                  │
                                  ├─── Priority: HIGH ──────┐
                                  │                         │
                                  │                    [Audit Logger]
                                  │                    (logs action)
                                  │                         │
                                  ├─── Priority: NORMAL ────┤
                                  │                         │
                                  │                    [Notifier]
                                  │                    (sends Discord msg)
                                  │                         │
                                  └─── Priority: LOW ───────┤
                                                            │
                                                       [Statistics]
                                                       (updates metrics)
```

## Event Categories

### User Events
- `UserCreatedEvent` - New user registered
- `UserUpdatedEvent` - User information changed
- `UserDeletedEvent` - User deactivated/deleted
- `UserPermissionChangedEvent` - Global permission level changed

### Organization Events
- `OrganizationCreatedEvent` - New organization created
- `OrganizationUpdatedEvent` - Organization settings changed
- `OrganizationDeletedEvent` - Organization deactivated
- `OrganizationMemberAddedEvent` - User joined organization
- `OrganizationMemberRemovedEvent` - User left/removed from org
- `OrganizationMemberPermissionChangedEvent` - Member's org permissions changed

### Tournament Events
- `TournamentCreatedEvent` - New tournament created
- `TournamentUpdatedEvent` - Tournament settings changed
- `TournamentDeletedEvent` - Tournament deleted
- `TournamentStartedEvent` - Tournament officially begins (HIGH priority)
- `TournamentEndedEvent` - Tournament completed (HIGH priority)

### Match/Race Events
- `RaceSubmittedEvent` - Player submitted race result
- `RaceApprovedEvent` - Reviewer approved submission
- `RaceRejectedEvent` - Reviewer rejected submission
- `MatchScheduledEvent` - Match scheduled
- `MatchCompletedEvent` - Match finished

### Invite Events
- `InviteCreatedEvent` - Organization invite created
- `InviteAcceptedEvent` - Invite accepted
- `InviteRejectedEvent` - Invite rejected
- `InviteExpiredEvent` - Invite expired (LOW priority)

## Usage Guide

### Emitting Events from Services

Events should be emitted **after** successful database operations in service methods:

```python
from application.events import EventBus, UserCreatedEvent

class UserService:
    async def create_user(self, discord_id: int, username: str) -> User:
        # 1. Perform the operation
        user = await self.user_repository.create(
            discord_id=discord_id,
            discord_username=username
        )

        # 2. Emit the event (fire-and-forget)
        from models import SYSTEM_USER_ID
        
        event = UserCreatedEvent(
            entity_id=user.id,
            user_id=SYSTEM_USER_ID,  # System action (no acting user)
            organization_id=None,  # Not org-specific
            discord_id=discord_id,
            discord_username=username
        )
        await EventBus.emit(event)

        # 3. Return the result
        return user
```

### Registering Event Listeners

Use the `@EventBus.on()` decorator to register handlers:

```python
from application.events import EventBus, EventPriority, UserCreatedEvent
import logging

logger = logging.getLogger(__name__)

@EventBus.on(UserCreatedEvent, priority=EventPriority.HIGH)
async def send_welcome_email(event: UserCreatedEvent) -> None:
    """Send welcome email when user is created."""
    # Access event data
    user_id = event.entity_id
    username = event.discord_username

    # Perform action
    logger.info("Sending welcome email to user %s (%s)", user_id, username)
    # await email_service.send_welcome(user_id)
```

### Event Priority Levels

Use priorities to control handler execution order:

- **CRITICAL (100)** - Security events, must process immediately
- **HIGH (75)** - Audit logging, important operational events
- **NORMAL (50)** - Standard handlers (notifications, etc.)
- **LOW (25)** - Background tasks (analytics, statistics)

Higher priority handlers run before lower priority handlers.

### Event Data Best Practices

**DO:**
- ✅ Include all context needed for handlers to operate independently
- ✅ Use immutable dataclasses (frozen=True)
- ✅ Include user_id and organization_id for audit context
- ✅ Snapshot relevant entity data in entity_data field
- ✅ Emit events AFTER successful database writes

**DON'T:**
- ❌ Emit events before database operations (they might fail)
- ❌ Put business logic in event handlers (keep them simple)
- ❌ Make handlers dependent on each other
- ❌ Raise exceptions from handlers (they're logged and isolated)
- ❌ Query the database for data that could be in the event

## Testing

### Disabling Events in Tests

```python
from application.events import EventBus

def test_my_service():
    # Disable event processing
    EventBus.disable()

    # Run test
    result = await service.create_user(...)

    # Re-enable
    EventBus.enable()
```

### Testing Event Handlers

```python
import pytest
from application.events import EventBus, UserCreatedEvent

@pytest.mark.asyncio
async def test_user_created_handler():
    # Create event
    event = UserCreatedEvent(
        entity_id=123,
        discord_id=456,
        discord_username="testuser"
    )

    # Clear handlers and register test handler
    EventBus.clear_all()

    called = False

    @EventBus.on(UserCreatedEvent)
    async def test_handler(e: UserCreatedEvent):
        nonlocal called
        called = True
        assert e.entity_id == 123

    # Emit and verify
    await EventBus.emit(event)
    assert called
```

## Current Listeners

### Audit Logging (HIGH Priority)
Automatically creates audit log entries for:
- User creation, permission changes
- Organization creation, member additions/removals
- Tournament creation
- Race submissions and approvals

Located in `application/events/listeners.py`

## Future Expansion

The event system is designed for easy extension. Planned features:

### Notification System
- Discord notifications for tournament events
- Email notifications for important actions
- In-app notification center
- User notification preferences

### Analytics & Statistics
- Real-time tournament statistics
- User activity tracking
- Performance metrics
- Leaderboard updates

### Discord Announcements
- Tournament start/end announcements
- Race approval notifications
- Organization activity feeds

### Webhook Support
- External webhook integrations
- Custom event subscriptions
- API event streaming

## Adding New Events

1. **Define Event Type** in `application/events/types.py`:

```python
@dataclass(frozen=True)
class MyNewEvent(EntityEvent):
    """Emitted when something happens."""
    entity_type: str = field(default="MyEntity", init=False)
    custom_field: Optional[str] = None
```

2. **Export** from `application/events/__init__.py`:

```python
from application.events.types import MyNewEvent
__all__ = [..., "MyNewEvent"]
```

3. **Emit** from service layer:

```python
event = MyNewEvent(
    entity_id=entity.id,
    user_id=current_user.id,
    organization_id=org_id,
    custom_field="value"
)
await EventBus.emit(event)
```

4. **Handle** in listener (optional):

```python
@EventBus.on(MyNewEvent)
async def handle_my_event(event: MyNewEvent):
    logger.info("Event occurred: %s", event.custom_field)
```

## Troubleshooting

### Events Not Firing
- Check that `application.events.listeners` is imported in `main.py`
- Verify EventBus is enabled: `EventBus.is_enabled()`
- Ensure event is being emitted: add logging before `EventBus.emit()`

### Handler Not Called
- Verify handler is registered: `EventBus.get_handler_count(MyEvent)`
- Check event type matches exactly
- Look for exceptions in handler (check logs)

### Performance Issues
- Lower priority of background handlers
- Avoid heavy operations in handlers
- Consider moving work to background tasks/queue

## Best Practices Summary

1. **Emit After Success** - Only emit events after database operations succeed
2. **Include Context** - Put all necessary data in the event
3. **Stay Simple** - Keep handlers focused on single responsibility
4. **Use Priorities** - Order handlers appropriately
5. **Log Everything** - Use structured logging in handlers
6. **Test Thoroughly** - Unit test both emission and handling
7. **Document Events** - Update this guide when adding new event types

---

For more information, see:
- `application/events/base.py` - Event base classes
- `application/events/bus.py` - EventBus implementation
- `application/events/types.py` - Event type definitions
- `application/events/listeners.py` - Current event handlers
