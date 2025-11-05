# Async Tournament Task Scheduler Migration

## Overview

This document describes the migration from discord.py's built-in task scheduler to SahaBot2's unified task scheduler for async tournament background operations.

## What Changed

### Before
The async tournament Discord bot commands (`discordbot/commands/async_tournament.py`) used discord.py's `@tasks.loop()` decorators to run three background tasks:

1. **timeout_pending_races** - Ran every 60 seconds to check pending races
2. **timeout_in_progress_races** - Ran every 60 seconds to check in-progress races
3. **score_calculation** - Ran every hour to recalculate tournament scores

These tasks were managed by discord.py's extension framework and started/stopped with the cog lifecycle.

### After
All three background tasks now use SahaBot2's unified task scheduler system:

1. **New Task Types** added to `TaskType` enum in `models/scheduled_task.py`:
   - `ASYNC_TOURNAMENT_TIMEOUT_PENDING`
   - `ASYNC_TOURNAMENT_TIMEOUT_IN_PROGRESS`
   - `ASYNC_TOURNAMENT_SCORE_CALCULATION`

2. **Task Handlers** created in `application/services/task_handlers.py`:
   - `handle_async_tournament_timeout_pending()` - Checks pending races and sends warnings/forfeits
   - `handle_async_tournament_timeout_in_progress()` - Checks in-progress races for 12-hour timeout
   - `handle_async_tournament_score_calculation()` - Recalculates scores for active tournaments

3. **Built-in Tasks** defined in `application/services/builtin_tasks.py`:
   - `async_tournament_timeout_pending` - Runs every minute
   - `async_tournament_timeout_in_progress` - Runs every minute
   - `async_tournament_score_calculation` - Runs every hour

4. **Discord Bot Simplified** - The `AsyncTournamentCommands` cog no longer manages background tasks:
   - Removed `@tasks.loop()` decorators
   - Removed task start/stop logic from `__init__` and `cog_unload`
   - Discord bot now only handles user commands and views

## Benefits

### 1. Centralized Task Management
All scheduled tasks (tournament cleanup, score calculation, race timeouts, etc.) are managed through a single unified system, making it easier to:
- Monitor all scheduled tasks in one place
- View task execution history and status
- Enable/disable tasks without code changes
- Adjust schedules without redeploying

### 2. Better Observability
The task scheduler provides:
- Database tracking of task execution (last run time, status, errors)
- Audit logs for task operations
- Unified logging across all task types
- Easy access to task configuration and status via API/UI

### 3. Separation of Concerns
- **Discord bot** focuses on user interactions (commands, views, messages)
- **Task scheduler** handles all background automation
- Clear architectural boundaries make the codebase easier to understand and maintain

### 4. Reliability
- Tasks continue running even if Discord bot restarts
- Task state persists in database
- Failed tasks are logged with detailed error information
- Easy to retry failed tasks or adjust schedules

### 5. Flexibility
Task configurations can be customized via `task_config`:
```python
{
    "warning_minutes": 10,  # Minutes before forfeit to send warning
    "timeout_minutes": 20,  # Minutes until forfeit
}
```

Administrators can create custom schedules per-organization if needed (e.g., different timeout periods for different tournaments).

## Task Details

### Timeout Pending Races
- **Task ID**: `async_tournament_timeout_pending`
- **Schedule**: Every 60 seconds
- **Function**: Checks all pending races with Discord threads
- **Actions**:
  - Sets default timeout (20 minutes) if not already set
  - Sends warning 10 minutes before forfeit
  - Auto-forfeits races that exceed timeout
  - Creates audit logs for all actions

**Configuration**:
```json
{
    "warning_minutes": 10,
    "timeout_minutes": 20
}
```

### Timeout In-Progress Races
- **Task ID**: `async_tournament_timeout_in_progress`
- **Schedule**: Every 60 seconds
- **Function**: Checks all in-progress races
- **Actions**:
  - Auto-forfeits races exceeding 12 hours
  - Sends Discord notification to user
  - Creates audit logs for forfeit actions

**Configuration**:
```json
{
    "max_hours": 12
}
```

### Score Calculation
- **Task ID**: `async_tournament_score_calculation`
- **Schedule**: Every 60 minutes
- **Function**: Recalculates scores for active tournaments
- **Actions**:
  - Fetches all active async tournaments
  - Recalculates par times for each permalink
  - Updates race scores based on new par times
  - Handles errors per-tournament (failure in one doesn't affect others)

**Configuration**:
```json
{
    "tournament_ids": [1, 2, 3]  // Optional: specific tournament IDs
}
```

If `tournament_ids` is not provided, recalculates for ALL active tournaments.

## Migration Steps (Already Completed)

1. ✅ Added new `TaskType` enum values
2. ✅ Created task handler functions in `task_handlers.py`
3. ✅ Registered new handlers in `register_task_handlers()`
4. ✅ Defined built-in tasks in `builtin_tasks.py`
5. ✅ Removed discord.py task decorators from bot commands
6. ✅ Removed task lifecycle management from cog
7. ✅ Created database migration (enum-only, no schema changes)

## Usage

### Viewing Tasks
Tasks are automatically loaded at application startup. View them via:
- **Web UI**: Organizations > Scheduled Tasks tab
- **API**: `GET /api/scheduled-tasks/builtin`

### Monitoring
Check task execution status:
- Last run time
- Last run status (success/failed)
- Error messages (if failed)
- Next scheduled run time

### Customization
To create a custom schedule for an organization:
1. Go to Organizations > Scheduled Tasks
2. Click "Add Task"
3. Select task type (e.g., "Async Tournament Score Calculation")
4. Configure schedule (interval or cron)
5. Set organization scope
6. Adjust task_config as needed

## Troubleshooting

### Tasks Not Running
1. Check if task scheduler is running: `TaskSchedulerService.is_running()`
2. Verify task is active: Check `is_active` field
3. Check logs for errors: Look for task handler exceptions
4. Verify next_run_at is set correctly

### Race Timeouts Not Working
1. Ensure Discord bot is running and connected
2. Check `discord_thread_id` is set on races
3. Verify bot has permission to access/message threads
4. Check task execution logs for errors

### Scores Not Updating
1. Verify tournaments are marked as `is_active=True`
2. Check for errors in score calculation logs
3. Ensure races have elapsed_time set
4. Verify par_time is calculated for permalinks

## Code References

- **Task Types**: `models/scheduled_task.py`
- **Task Handlers**: `application/services/task_handlers.py`
- **Built-in Tasks**: `application/services/builtin_tasks.py`
- **Task Scheduler Service**: `application/services/task_scheduler_service.py`
- **Discord Commands**: `discordbot/commands/async_tournament.py`

## Future Enhancements

Potential improvements to the async tournament task system:

1. **Per-Tournament Timeouts**: Allow tournaments to override global timeout settings
2. **Notification Preferences**: Let users opt-in/out of timeout warnings
3. **Score Calculation Triggers**: Calculate scores immediately after race submission (not just hourly)
4. **Task Metrics**: Track task execution duration, success rate, etc.
5. **Dynamic Scheduling**: Adjust task frequency based on tournament activity

## Notes

- Built-in tasks are defined in code and loaded at startup (not stored in database)
- Organizations can create custom instances of these task types with different schedules
- The Discord bot is no longer responsible for task scheduling - it only handles user interactions
- All task handlers have access to the Discord bot instance via `get_bot_instance()`
