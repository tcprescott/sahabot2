# RaceTime Event System - Implementation Summary

## Overview
This document summarizes the complete RaceTime event system implementation, including user ID resolution and the SYSTEM_USER_ID security pattern.

## Features Implemented

### 1. Core Event Types
**Entrant Events:**
- `RacetimeEntrantJoinedEvent` - Player joins a race room
- `RacetimeEntrantLeftEvent` - Player leaves a race room
- `RacetimeEntrantStatusChangedEvent` - Player status changes (ready, not_ready, done, etc.)
- `RacetimeEntrantInvitedEvent` - Bot invites a player to a race room

**Bot Action Events:**
- `RacetimeBotJoinedRaceEvent` - Bot joins an existing race room
- `RacetimeBotCreatedRaceEvent` - Bot creates a new race room

**Race Status Events:**
- `RacetimeRaceStatusChangedEvent` - Race status changes (pending, in_progress, finished, cancelled)

### 2. User ID Resolution
All entrant events include a `user_id` field that links racetime.gg users to application users:

```python
@dataclass
class RacetimeEntrantJoinedEvent(BaseEvent):
    """Event emitted when an entrant joins a race room."""
    race_slug: str
    racetime_id: str
    display_name: str
    status: str
    user_id: Optional[int] = None  # Application user ID (None if racetime account not linked)
```

**User ID Resolution Logic:**
- **Positive ID** (1, 2, 42, etc.): User's racetime.gg account is linked to their application account
- **SYSTEM_USER_ID** (-1): System/automation action (bot actions, race status changes)
- **None**: Racetime account not linked to any application user (unknown/unauthenticated)

### 3. SYSTEM_USER_ID Security Pattern
A sentinel constant (`SYSTEM_USER_ID = -1`) explicitly identifies system automation vs. unauthenticated users:

```python
from models import SYSTEM_USER_ID, is_system_user_id, is_authenticated_user_id

# Check user type
if is_authenticated_user_id(event.user_id):
    # Linked application user - can authorize
    pass
elif is_system_user_id(event.user_id):
    # System automation - bypass user authorization
    pass
else:  # user_id is None
    # Unknown/unauthenticated - deny
    pass
```

## Security Considerations

### Authorization Pattern
**CRITICAL:** Never treat `None` as a system action. Always check explicitly:

```python
# ✅ CORRECT - Explicit system check
if is_system_user_id(user_id):
    # System automation - allowed
    perform_admin_action()
elif is_authenticated_user_id(user_id):
    # Check user permissions
    if user.has_permission(Permission.ADMIN):
        perform_admin_action()
else:
    # Unknown user - deny
    raise PermissionError("Authentication required")

# ❌ WRONG - Confuses None with system
if user_id is None:
    # This could be either system OR unknown!
    perform_admin_action()  # SECURITY RISK
```

### Three-State Pattern Benefits
1. **Explicit System Actions**: `SYSTEM_USER_ID` clearly indicates automation
2. **Unknown Users**: `None` indicates racetime account not linked
3. **Authenticated Users**: Positive ID enables permission checks
4. **Audit Trail**: `get_user_id_description()` provides clear logging

## Event Emission Patterns

### System Events (Use SYSTEM_USER_ID)
```python
# Bot creates/joins races
await EventBus.emit(RacetimeBotCreatedRaceEvent(
    race_slug=race_slug,
    user_id=SYSTEM_USER_ID,  # System automation
))

# Race status changes (automated)
await EventBus.emit(RacetimeRaceStatusChangedEvent(
    race_slug=race_slug,
    old_status="pending",
    new_status="in_progress",
    user_id=SYSTEM_USER_ID,  # System automation
))
```

### User Events (Use Lookup)
```python
# Entrant joins/leaves/changes status
user_id = await self._get_user_id_from_racetime_id(racetime_id)  # Returns ID or None
await EventBus.emit(RacetimeEntrantJoinedEvent(
    race_slug=race_slug,
    racetime_id=racetime_id,
    display_name=display_name,
    status=status,
    user_id=user_id,  # Positive ID if linked, None if not
))
```

## Testing
All functionality verified with comprehensive test coverage:
- ✅ 10/10 tests passing
- ✅ Race status changes use SYSTEM_USER_ID
- ✅ Bot actions use SYSTEM_USER_ID
- ✅ User lookup returns positive ID for linked accounts
- ✅ User lookup returns None for unlinked accounts
- ✅ All event fields populated correctly
- ✅ Event handlers receive events properly

## Documentation

### Primary Guides
- **[RACETIME_RACE_EVENTS.md](RACETIME_RACE_EVENTS.md)**: Complete event reference
- **[SYSTEM_USER_ID.md](SYSTEM_USER_ID.md)**: SYSTEM_USER_ID pattern guide
- **[examples/system_user_id_example.py](examples/system_user_id_example.py)**: Practical usage examples

### Helper Functions
```python
from models import (
    SYSTEM_USER_ID,
    is_system_user_id,
    is_authenticated_user_id,
    get_user_id_description,
)

# Type checking
is_system_user_id(-1)  # True
is_system_user_id(None)  # False
is_authenticated_user_id(42)  # True
is_authenticated_user_id(-1)  # False

# Logging/auditing
get_user_id_description(42)  # "User 42"
get_user_id_description(SYSTEM_USER_ID)  # "System/Automation"
get_user_id_description(None)  # "Unknown/Unauthenticated"
```

## Implementation Files

### Core Implementation
- `racetime/client.py`: Event emission in race handler
- `application/events/types.py`: Event type definitions
- `models/user.py`: SYSTEM_USER_ID constant and helper functions
- `application/repositories/user_repository.py`: User lookup by racetime_id

### Tests
- `tests/test_racetime_status_events.py`: Comprehensive event tests (10 tests)

### Documentation
- `docs/RACETIME_RACE_EVENTS.md`: Event reference guide
- `docs/SYSTEM_USER_ID.md`: Security pattern guide
- `docs/examples/system_user_id_example.py`: Practical examples

## Usage Examples

### Event Handler with Authorization
```python
from application.events import EventBus, RacetimeEntrantJoinedEvent
from application.services.match_service import MatchService
from models import is_authenticated_user_id

@EventBus.subscribe(RacetimeEntrantJoinedEvent)
async def handle_entrant_joined(event: RacetimeEntrantJoinedEvent):
    """Handle entrant joining a race room."""
    
    # Only process for linked users
    if not is_authenticated_user_id(event.user_id):
        logger.info("Ignoring join from unlinked racetime account: %s", event.racetime_id)
        return
    
    # User is authenticated - can perform authorized actions
    match_service = MatchService()
    await match_service.auto_register_for_race(
        user_id=event.user_id,
        race_slug=event.race_slug,
    )
```

### Bot Command with User Lookup
```python
@bot.race_command('!ready')
async def ready_command(handler: RaceHandler, args: List[str]):
    """Mark user as ready (requires linked account)."""
    
    # Get racetime ID from message sender
    racetime_id = handler.data.get('user', {}).get('id')
    
    # Look up application user
    user_repo = UserRepository()
    user_id = await user_repo.get_id_by_racetime_id(racetime_id)
    
    if not is_authenticated_user_id(user_id):
        await handler.send_message("You must link your racetime.gg account first.")
        return
    
    # User is authenticated - perform action
    match_service = MatchService()
    await match_service.mark_ready(user_id, handler.data['name'])
    await handler.send_message(f"Marked as ready!")
```

## Migration Notes

### For Existing Code Using `user_id=None`
If you have existing code that uses `user_id=None` for system actions:

```python
# ❌ Old pattern (ambiguous)
await EventBus.emit(SomeEvent(
    user_id=None,  # Is this system or unknown?
))

# ✅ New pattern (explicit)
from models import SYSTEM_USER_ID

await EventBus.emit(SomeEvent(
    user_id=SYSTEM_USER_ID,  # Clearly system automation
))
```

### For Authorization Checks
Update authorization checks to handle all three states:

```python
# ❌ Old pattern (security risk)
if user_id is None:
    # Allow system actions?? Or deny unknown users??
    pass

# ✅ New pattern (secure)
from models import is_system_user_id, is_authenticated_user_id

if is_system_user_id(user_id):
    # Explicit system action
    pass
elif is_authenticated_user_id(user_id):
    # Check user permissions
    pass
else:
    # user_id is None - unknown/unauthenticated
    raise PermissionError("Authentication required")
```

## Next Steps

### Production Deployment
1. ✅ All tests passing - ready for production
2. ✅ Documentation complete
3. ✅ Security pattern implemented
4. Optional: Add database migration to update historical audit logs

### Future Enhancements
- Consider webhook integration for external services
- Add event replay/debugging tools
- Implement event statistics/monitoring dashboard
- Create admin UI for viewing event history

## Questions & Support

For implementation details:
- See [RACETIME_RACE_EVENTS.md](RACETIME_RACE_EVENTS.md) for event reference
- See [SYSTEM_USER_ID.md](SYSTEM_USER_ID.md) for security pattern guide
- See [examples/system_user_id_example.py](examples/system_user_id_example.py) for code examples

For testing:
```bash
poetry run pytest tests/test_racetime_status_events.py -v
```

---
**Status**: ✅ Complete and Production-Ready  
**Last Updated**: 2025-01-04  
**Test Coverage**: 10/10 tests passing
