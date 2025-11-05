# SYSTEM_USER_ID Migration Summary

## Overview
This document summarizes the migration from using `None` to indicate system actions to using the explicit `SYSTEM_USER_ID` sentinel constant (-1).

## Motivation
Using `None` for system actions created security ambiguity:
- **Problem**: `None` could mean either "system action" OR "unknown/unauthenticated user"
- **Risk**: Authorization code couldn't distinguish between legitimate automation and missing authentication
- **Solution**: Use `SYSTEM_USER_ID = -1` for explicit system identification

## Three-State User ID Pattern

### States
1. **Positive ID** (1, 2, 42, etc.): Authenticated user with application account
2. **SYSTEM_USER_ID** (-1): System automation (scheduled tasks, bot actions, OAuth flow)
3. **None**: Unknown/unauthenticated user (racetime accounts not linked, missing auth)

### Helper Functions
```python
from models import (
    SYSTEM_USER_ID,
    is_system_user_id,         # Returns True if user_id == -1
    is_authenticated_user_id,  # Returns True if user_id is not None and > 0
    get_user_id_description,   # Returns human-readable string
)
```

## Files Modified

### Core Implementation
1. **`models/user.py`**
   - Added `SYSTEM_USER_ID = -1` constant
   - Added helper functions: `is_system_user_id()`, `is_authenticated_user_id()`, `get_user_id_description()`

2. **`models/__init__.py`**
   - Exported `SYSTEM_USER_ID` and helper functions

### Service Layer
3. **`application/services/user_service.py`**
   - Updated `get_or_create_user()`: Changed `user_id=None` → `user_id=SYSTEM_USER_ID` for OAuth user creation
   - Comment: "System/OAuth action" (automated user creation)
   - **Note**: `create_user_manual()` keeps `user_id=None` (manual admin creation, acting user not tracked)

4. **`application/services/task_handlers.py`**
   - Updated `handle_async_tournament_timeout_pending()`: Changed audit log `user_id=None` → `user_id=SYSTEM_USER_ID`
   - Updated `handle_async_tournament_timeout_in_progress()`: Changed audit log `user_id=None` → `user_id=SYSTEM_USER_ID`
   - Both are scheduled task handlers performing automated forfeit operations

5. **`application/services/audit_service.py`**
   - Updated docstring: "None for system actions" → "use SYSTEM_USER_ID for system actions, None for unknown"

### RaceTime Integration
6. **`racetime/client.py`**
   - Updated `RacetimeBotCreatedRaceEvent`: `user_id=SYSTEM_USER_ID` (bot creating race room)
   - Updated `RacetimeBotJoinedRaceEvent`: `user_id=SYSTEM_USER_ID` (bot joining race room)
   - Updated `RacetimeRaceStatusChangedEvent`: `user_id=SYSTEM_USER_ID` (automated status changes)

### Event Types
7. **`application/events/types.py`**
   - Added `user_id: Optional[int]` field to racetime entrant events
   - Comments indicate: "Application user ID (None if racetime account not linked)"

### Tests
8. **`tests/test_racetime_status_events.py`**
   - Updated assertions to verify `user_id == SYSTEM_USER_ID` for system events
   - Verified user_id lookup returns positive ID for linked accounts
   - Verified user_id is None for unlinked accounts

### Documentation
9. **`docs/RACETIME_RACE_EVENTS.md`**
   - Updated example code to use `SYSTEM_USER_ID` instead of `None`
   - Added "User ID Resolution" section explaining three-state pattern

10. **`docs/RACETIME_STATUS_EVENTS_IMPLEMENTATION.md`**
    - Updated example code to import and use `SYSTEM_USER_ID`

11. **`docs/EVENT_SYSTEM.md`**
    - Updated example code to import and use `SYSTEM_USER_ID`

12. **`docs/EVENT_SYSTEM_COMPLETE.md`**
    - Updated example code to import and use `SYSTEM_USER_ID`

13. **`docs/SYSTEM_USER_ID.md`** (NEW)
    - Comprehensive guide to SYSTEM_USER_ID pattern
    - Usage examples and authorization patterns
    - Security considerations and migration guide

14. **`docs/RACETIME_EVENT_SUMMARY.md`** (NEW)
    - Implementation summary with SYSTEM_USER_ID pattern

15. **`docs/examples/system_user_id_example.py`** (NEW)
    - Practical code examples for SYSTEM_USER_ID usage

## Usage Patterns

### Before (Ambiguous)
```python
# ❌ Could mean system OR unknown user
await EventBus.emit(SomeEvent(
    user_id=None,  # Is this system automation or unknown user?
))

# ❌ Authorization can't distinguish
if user_id is None:
    # Allow system? Or deny unknown user?
    pass
```

### After (Explicit)
```python
# ✅ Explicit system action
from models import SYSTEM_USER_ID

await EventBus.emit(SomeEvent(
    user_id=SYSTEM_USER_ID,  # Clearly system automation
))

# ✅ Clear authorization logic
from models import is_system_user_id, is_authenticated_user_id

if is_system_user_id(user_id):
    # System automation - bypass user checks
    pass
elif is_authenticated_user_id(user_id):
    # Check user permissions
    pass
else:
    # user_id is None - unknown/unauthenticated
    raise PermissionError("Authentication required")
```

## When to Use Each Value

### Use SYSTEM_USER_ID (-1)
- Scheduled tasks (auto-forfeit, cleanup, notifications)
- Bot actions (creating rooms, joining races, inviting players)
- Automated race status changes
- OAuth-triggered user creation
- System-initiated operations

### Use None
- Unknown users (racetime accounts not linked to app)
- Unauthenticated requests
- Manual admin actions where acting user isn't tracked
- Cases where user ID couldn't be determined

### Use Positive ID
- Authenticated users performing actions
- User-initiated operations
- Actions requiring permission checks
- Audit trail where user accountability matters

## Security Implications

### Before Migration
- **Risk**: Code treating `None` as system action could be exploited
- **Issue**: Can't audit-trail system vs unknown users
- **Problem**: Authorization checks ambiguous

### After Migration
- **Secure**: Explicit `is_system_user_id()` check required for system bypass
- **Auditable**: Clear distinction in logs between system and unknown
- **Safe**: Default deny for `None` (unknown users)

## Testing
All tests passing (10/10 in `tests/test_racetime_status_events.py`):
- ✅ Race status changes use `SYSTEM_USER_ID`
- ✅ Bot actions use `SYSTEM_USER_ID`
- ✅ Entrant events use user lookup (positive ID or None)
- ✅ Helper functions work correctly

## Rollout Plan

### Completed
1. ✅ Created `SYSTEM_USER_ID` constant and helper functions
2. ✅ Updated all system events to use `SYSTEM_USER_ID`
3. ✅ Updated all scheduled task audit logs to use `SYSTEM_USER_ID`
4. ✅ Updated all documentation with new pattern
5. ✅ Created comprehensive guides and examples
6. ✅ All tests passing

### Optional Future Work
- Consider database migration to update historical audit logs
  - Current: Historical `user_id=None` could be either system or unknown
  - Future: Could analyze action types to retroactively classify
  - Impact: Low priority - only affects historical data analysis

### Ongoing
- Use pattern for all new system automation
- Use pattern for all new event emissions
- Review existing services for additional system actions

## References
- [SYSTEM_USER_ID.md](SYSTEM_USER_ID.md) - Comprehensive pattern guide
- [RACETIME_RACE_EVENTS.md](RACETIME_RACE_EVENTS.md) - Event reference with user_id
- [RACETIME_EVENT_SUMMARY.md](RACETIME_EVENT_SUMMARY.md) - Implementation overview
- [examples/system_user_id_example.py](examples/system_user_id_example.py) - Code examples

---
**Migration Completed**: 2025-01-04  
**Status**: ✅ Production Ready  
**Test Coverage**: 10/10 tests passing
