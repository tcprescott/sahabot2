# RaceTime.gg Automatic Polling Disabled

## Overview

As of this change, SahaBot2 **explicitly disables** the automatic race room polling behavior from the upstream `racetime-bot` library. Instead, race rooms are joined explicitly via the task scheduler system or manual commands.

## Background

The upstream `racetime-bot` library (v2.3.0) includes an automatic polling mechanism via the `refresh_races()` method. This method:
- Polls racetime.gg for all active race rooms in the configured category
- Automatically joins race rooms based on the `should_handle()` method
- Creates handlers for each joined race room

While this works well for simple bots, it doesn't fit SahaBot2's architecture:
- We need precise control over when and how race rooms are joined
- We want scheduled race room creation at specific times
- We don't want the bot randomly joining public race rooms
- We have a task scheduler system that should handle all automation

## What Changed

### 1. `should_handle()` Always Returns False

**File**: `racetime/client.py`

```python
def should_handle(self, race_data: dict) -> bool:
    """
    Determine if this bot should handle a specific race.
    
    NOTE: This method is not used in SahaBot2. We do NOT use automatic race
    room polling/joining. Instead, race rooms are joined explicitly via the
    task scheduler system or manual commands.
    
    This method is kept for compatibility with the base Bot class, but always
    returns False to prevent automatic joining.
    """
    # Always return False - we use explicit joining via scheduler, not automatic polling
    return False
```

**Before**: Returned `True` for all races in the category
**After**: Always returns `False` to prevent automatic joining

### 2. `refresh_races()` Task Not Started

**File**: `racetime/client.py` (in `start_racetime_bot()`)

**Before**:
```python
reauth_task = asyncio.create_task(bot.reauthorize())
refresh_task = asyncio.create_task(bot.refresh_races())

await asyncio.gather(reauth_task, refresh_task)
```

**After**:
```python
# NOTE: We do NOT create the refresh_races() task here. In the original
# racetime-bot library, refresh_races() polls for race rooms and automatically
# joins them based on should_handle(). We explicitly disable this behavior
# because SahaBot2 uses the task scheduler system to join race rooms at
# scheduled times instead of automatic polling.
#
# Race rooms are joined explicitly via:
# - Scheduled tasks (task scheduler system)
# - Manual commands (!startrace, etc.)
# - API calls (startrace, join_race_room)
reauth_task = asyncio.create_task(bot.reauthorize())

await reauth_task
```

### 3. Updated Documentation

Added comprehensive documentation in the module docstring explaining:
- Why polling is disabled
- How race rooms are joined instead
- The architectural decision behind this change

## How Race Rooms Are Joined

With automatic polling disabled, race rooms are now joined **explicitly** via:

### 1. Task Scheduler System

Create a scheduled task to open race rooms at specific times:

```python
from application.services.task_scheduler_service import TaskSchedulerService
from models import TaskType, ScheduleType

service = TaskSchedulerService()

# Create a task to open a race room every hour
task = await service.create_task(
    user=current_user,
    organization_id=org_id,
    name="Hourly Race Room",
    task_type=TaskType.RACETIME_OPEN_ROOM,
    schedule_type=ScheduleType.INTERVAL,
    interval_seconds=3600,
    task_config={
        "category": "alttpr",
        "goal": "Beat the game",
    },
    is_active=True,
)
```

**See**: [`docs/systems/TASK_SCHEDULER.md`](../systems/TASK_SCHEDULER.md)

### 2. Manual Bot Commands

Users can create race rooms via Discord bot commands:

```
!startrace <goal>
```

### 3. API Calls

Race rooms can be created programmatically:

```python
bot = get_racetime_bot_instance("alttpr")
if bot:
    handler = await bot.startrace(
        goal="Beat the game",
        invitational=True,
        unlisted=False,
    )
```

Or joined explicitly:

```python
bot = get_racetime_bot_instance("alttpr")
if bot:
    handler = await bot.join_race_room("alttpr/cool-doge-1234")
```

## Benefits

This change provides several architectural benefits:

### 1. **Predictable Behavior**
- Race rooms are only joined when explicitly requested
- No surprise race room handlers created by polling
- Clear audit trail of who/what joined each race

### 2. **Scheduled Automation**
- Use task scheduler for precise timing (cron expressions, intervals)
- Schedule race rooms days/weeks in advance
- Centralized task management in the database

### 3. **Resource Efficiency**
- No continuous polling overhead
- Handlers only created when needed
- Reduces API calls to racetime.gg

### 4. **Multi-Tenant Control**
- Organizations control their own scheduled tasks
- No global race room joining logic
- Organization-scoped automation

### 5. **Compliance with Architecture**
- Follows SahaBot2's layered architecture
- Service layer controls business logic
- Task scheduler integrates with event system

## Migration Notes

If you were relying on automatic race room joining:

### Before (Automatic Polling)
```python
# Bot automatically joined all race rooms matching should_handle()
# No explicit control over which races to join
```

### After (Explicit Joining)
**Option 1: Scheduled Tasks**
```python
# Create a scheduled task in the database
task = await task_service.create_task(
    task_type=TaskType.RACETIME_OPEN_ROOM,
    schedule_type=ScheduleType.CRON,
    cron_expression="0 14 * * *",  # Daily at 2 PM
    task_config={"category": "alttpr", "goal": "Beat the game"},
)
```

**Option 2: Manual Join**
```python
# Explicitly join a specific race room
bot = get_racetime_bot_instance("alttpr")
handler = await bot.join_race_room("alttpr/cool-doge-1234")
```

## Testing

To verify polling is disabled:

1. Start a racetime bot for a category
2. Create a public race room on racetime.gg in that category
3. Verify the bot does NOT automatically join the race room
4. Create a scheduled task to join the race room
5. Verify the bot DOES join when the task executes

## Related Documentation

- **[Task Scheduler Guide](../systems/TASK_SCHEDULER.md)** - How to use the task scheduler
- **[RaceTime Integration](RACETIME_INTEGRATION.md)** - RaceTime.gg integration overview
- **[Architecture Guide](../ARCHITECTURE.md)** - System architecture and patterns

## Troubleshooting

### Bot Not Joining Race Rooms

**Symptom**: Bot is running but not joining any race rooms

**Diagnosis**:
- This is expected behavior! Polling is disabled.
- Race rooms must be joined explicitly.

**Solution**:
- Create a scheduled task to open/join race rooms
- Use manual commands (!startrace)
- Call `bot.startrace()` or `bot.join_race_room()` via API

### Want Automatic Joining

**Symptom**: You want the bot to automatically join all race rooms in a category

**Diagnosis**:
- This is not supported with the current architecture
- Automatic joining conflicts with multi-tenant model

**Solution**:
- Use scheduled tasks with frequent intervals (e.g., every 5 minutes)
- Or, modify `should_handle()` to return True and re-enable `refresh_races()` task
  - **NOT RECOMMENDED** - breaks architectural patterns

## Future Enhancements

Potential improvements while keeping explicit control:

1. **Monitor Mode**: Bot monitors race rooms without joining (read-only)
2. **Smart Scheduling**: Automatically create tasks based on tournament schedules
3. **Race Room Templates**: Pre-configured task templates for common scenarios
4. **Bulk Task Creation**: Create multiple scheduled tasks at once
5. **Task Cloning**: Clone existing tasks with new schedules

---

**Last Updated**: November 4, 2025
