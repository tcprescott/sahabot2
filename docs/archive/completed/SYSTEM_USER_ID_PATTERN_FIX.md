# SYSTEM_USER_ID Pattern Fix

## Issue
The `async_live_race_service.py` was using `user_id=None` for system-initiated events, which violates the project's SYSTEM_USER_ID pattern.

## Changes Made

### 1. Updated `async_live_race_service.py`

**Import Added:**
```python
from models import User, SYSTEM_USER_ID
```

**Events Fixed:**

1. **AsyncLiveRaceRoomOpenedEvent** (line ~512):
   - Changed from: `user_id=None  # System action`
   - Changed to: `user_id=SYSTEM_USER_ID  # System action`

2. **AsyncLiveRaceStartedEvent** (line ~550):
   - Changed from: `user_id=None  # System action`
   - Changed to: `user_id=SYSTEM_USER_ID  # System action`

3. **AsyncLiveRaceFinishedEvent** (line ~622):
   - Changed from: `user_id=None  # System action`
   - Changed to: `user_id=SYSTEM_USER_ID  # System action`

### 2. Updated Copilot Instructions

**Added to Event System section:**
```markdown
- **System actions use SYSTEM_USER_ID**:
  - For automated/background operations (task scheduler, bots, system triggers)
  - Import from models: `from models import SYSTEM_USER_ID`
  - **Never use `None` for user_id in events** - always use SYSTEM_USER_ID for system actions
  ```python
  # ✅ Correct - system action (task scheduler, bot, automation)
  from models import SYSTEM_USER_ID
  
  await EventBus.emit(AsyncLiveRaceRoomOpenedEvent(
      user_id=SYSTEM_USER_ID,  # System action
      organization_id=org_id,
      entity_id=race_id,
      ...
  ))
  
  # ❌ Wrong - never use None for user_id
  await EventBus.emit(SomeEvent(
      user_id=None,  # Don't do this!
      ...
  ))
  ```
```

**Added to Event Best Practices:**
- Use `user_id=current_user.id` for user-initiated actions
- Use `user_id=SYSTEM_USER_ID` for system/automated actions

**Added to Common Pitfalls:**
- ❌ Don't use `None` for user_id in events - use `SYSTEM_USER_ID` for system/automated actions

## Why This Matters

1. **Audit Trail**: SYSTEM_USER_ID (-1) provides a clear indicator in audit logs that an action was system-initiated rather than user-initiated

2. **Type Safety**: Using SYSTEM_USER_ID (int) instead of None prevents potential null reference issues and maintains consistent typing

3. **Query Filtering**: Database queries can properly filter on user_id without special null handling

4. **Event Handlers**: Event handlers can reliably check if an action was system-initiated: `if event.user_id == SYSTEM_USER_ID:`

5. **Consistency**: All system actions across the application now follow the same pattern

## Pattern Usage

**When to use SYSTEM_USER_ID:**
- Task scheduler executing automated tasks
- Discord bot performing background operations
- RaceTime.gg handlers processing race events
- Automated cleanup/maintenance operations
- System-triggered notifications
- Cron jobs and scheduled tasks

**When to use current_user.id:**
- User clicking a button in the UI
- User submitting a form
- User calling an API endpoint
- Admin performing manual actions
- Any action directly initiated by a user

## Related Files
- `/Users/tprescott/Library/CloudStorage/OneDrive-Personal/Documents/VSCode/sahabot2/models/__init__.py` - Defines SYSTEM_USER_ID constant
- `/Users/tprescott/Library/CloudStorage/OneDrive-Personal/Documents/VSCode/sahabot2/models/user.py` - SYSTEM_USER_ID = -1
- `.github/copilot-instructions.md` - Updated documentation

## Verification
All linting errors cleared. The pattern is now consistently applied in:
- `async_live_race_service.py` - 3 event emissions fixed
- Copilot instructions updated with examples and warnings
- Common pitfalls list updated
