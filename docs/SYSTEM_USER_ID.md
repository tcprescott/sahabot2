# SYSTEM_USER_ID Pattern

## Overview

The `SYSTEM_USER_ID` constant (`-1`) is used to distinguish **automated system actions** from **unauthenticated/unknown users** in events and audit logs.

## Problem Statement

In event-driven systems, it's important to distinguish between:
1. **Authenticated user actions** - A known user performed an action
2. **System/automation actions** - The system performed an action automatically (e.g., bot created a race room)
3. **Unauthenticated/unknown actions** - An action occurred but we don't know which user performed it

Using `None` for both system actions and unknown users creates a security risk where an unauthenticated request might be confused with a legitimate system action.

## Solution: Sentinel Value

We use a sentinel value `SYSTEM_USER_ID = -1` to explicitly indicate system actions:

```python
from models import SYSTEM_USER_ID

# Three distinct states:
user_id = 42              # Authenticated user
user_id = SYSTEM_USER_ID  # System automation (-1)
user_id = None            # Unknown/unauthenticated
```

## Usage in Events

### System Automation Events

Use `SYSTEM_USER_ID` for events triggered by automated processes:

```python
# Bot creating a race room
await EventBus.emit(RacetimeBotCreatedRaceEvent(
    user_id=SYSTEM_USER_ID,  # System automation
    entity_id=room_slug,
    # ... other fields
))

# Race status change (automated by racetime.gg)
await EventBus.emit(RacetimeRaceStatusChangedEvent(
    user_id=SYSTEM_USER_ID,  # System automation
    entity_id=room_slug,
    old_status='pending',
    new_status='in_progress',
    # ... other fields
))
```

### User Actions (with lookup)

For user-triggered events, attempt to resolve the application user ID:

```python
# Look up application user from racetime ID
app_user_id = await self._get_user_id_from_racetime_id(racetime_user_id)

await EventBus.emit(RacetimeEntrantJoinedEvent(
    user_id=app_user_id,  # Positive ID if linked, None if not
    racetime_user_id=racetime_user_id,
    # ... other fields
))
```

## Helper Functions

The `models.user` module provides helper functions for working with user IDs:

### `is_system_user_id(user_id: Optional[int]) -> bool`

Check if a user_id represents a system action:

```python
from models import is_system_user_id

if is_system_user_id(event.user_id):
    logger.info("System automation triggered event")
    # Don't perform user-specific authorization checks
```

### `is_authenticated_user_id(user_id: Optional[int]) -> bool`

Check if a user_id represents an authenticated user:

```python
from models import is_authenticated_user_id

if is_authenticated_user_id(event.user_id):
    # Safe to use for authorization
    user = await user_repository.get_by_id(event.user_id)
    if authorization_service.can_manage_tournament(user, org_id):
        # Perform authorized action
        pass
```

### `get_user_id_description(user_id: Optional[int]) -> str`

Get a human-readable description for logging/auditing:

```python
from models import get_user_id_description

description = get_user_id_description(event.user_id)
logger.info("Action by: %s", description)
# Outputs: "User 42", "System/Automation", or "Unknown/Unauthenticated"
```

## Authorization Patterns

### Service Layer Authorization

When handling events in services, check the user_id type:

```python
from models import is_authenticated_user_id, SYSTEM_USER_ID

async def handle_race_finish(event: RacetimeEntrantStatusChangedEvent):
    if is_authenticated_user_id(event.user_id):
        # Real user - perform authorization checks
        if await auth_service.can_update_tournament(event.user_id, org_id):
            await tournament_service.record_result(event.user_id, event.match_id, ...)
    elif event.user_id == SYSTEM_USER_ID:
        # System action - may bypass user checks but still verify context
        logger.info("System recorded result for match %s", event.match_id)
    else:
        # Unknown user - log and skip
        logger.warning("Unlinked racetime user %s finished race", event.racetime_user_id)
```

### Bot Command Authorization

When handling bot commands from racetime chat:

```python
async def handle_bot_command(racetime_user_id: str, command: str):
    # Look up application user
    user_id = await get_user_id_from_racetime_id(racetime_user_id)
    
    if not is_authenticated_user_id(user_id):
        return "Please link your racetime account to use this command"
    
    # Perform authorization check
    if await auth_service.can_manage_tournament(user_id, org_id):
        # Execute privileged command
        pass
    else:
        return "You don't have permission to use this command"
```

## Audit Logging

When creating audit log entries, preserve the user_id type:

```python
from models import SYSTEM_USER_ID, get_user_id_description

await audit_service.log_action(
    user_id=event.user_id,  # Could be positive, SYSTEM_USER_ID, or None
    action="race_created",
    details={
        "room_slug": event.room_slug,
        "actor": get_user_id_description(event.user_id),
    }
)
```

## When to Use Each Value

| Scenario | user_id Value | Rationale |
|----------|---------------|-----------|
| Bot creates race room | `SYSTEM_USER_ID` | Automated bot action |
| Bot joins race room | `SYSTEM_USER_ID` | Automated bot action |
| Race status changes | `SYSTEM_USER_ID` | Automated by racetime.gg |
| Player joins (linked account) | Positive ID (e.g., 42) | Authenticated user action |
| Player joins (unlinked account) | `None` | Unknown user (not linked) |
| Player finishes (linked) | Positive ID | Authenticated user action |
| Player finishes (unlinked) | `None` | Unknown user |
| Bot invites player (linked) | Positive ID | Invitation target is known user |
| Bot invites player (unlinked) | `None` | Invitation target is unknown |

## Security Considerations

1. **Never trust `None` as system**: Always use `is_system_user_id()` to check for system actions
2. **Validate authenticated users**: Use `is_authenticated_user_id()` before authorization checks
3. **Audit trail**: Log `get_user_id_description()` for clear audit trails
4. **Service layer enforcement**: Always check user_id type in service methods, not just in event handlers

## Migration from None-based Pattern

If you have existing code using `user_id=None` for system actions:

```python
# ❌ Old pattern (ambiguous)
await EventBus.emit(SomeEvent(
    user_id=None,  # Could mean system OR unknown user
    # ...
))

# ✅ New pattern (explicit)
await EventBus.emit(SomeEvent(
    user_id=SYSTEM_USER_ID,  # Clearly indicates system action
    # ...
))
```

Update your event handlers to distinguish the cases:

```python
# ❌ Old pattern (treats both as same)
if event.user_id is None:
    # Can't tell if system or unknown user!
    pass

# ✅ New pattern (explicit handling)
if is_system_user_id(event.user_id):
    # System automation
    pass
elif event.user_id is None:
    # Unknown user
    pass
else:
    # Authenticated user
    pass
```

## See Also

- [Event System Documentation](EVENT_SYSTEM.md)
- [RaceTime Race Events](RACETIME_RACE_EVENTS.md)
- [Service Authorization Analysis](SERVICE_AUTHORIZATION_ANALYSIS.md)
