# Tournament Usage Tracking - Cleanup & Maintenance

## Overview

The tournament usage tracking feature records when users access tournaments to provide quick links on the home page. To prevent the `tournament_usage` table from growing indefinitely, an automatic cleanup system has been implemented as a **built-in task**.

## Built-in Task System

The cleanup runs as a **built-in task** - a task defined in code rather than in the database. Built-in tasks:
- Are loaded automatically at application startup
- Don't require manual setup or database configuration
- Are global (not scoped to any organization)
- Can be viewed but not edited through the UI

## Cleanup Strategies

The system supports two complementary cleanup strategies:

### 1. Age-Based Cleanup
- **Default**: Keeps entries from the last **90 days**
- **Purpose**: Removes very old entries that are no longer relevant
- **Configurable**: Can be adjusted via task configuration

### 2. Count-Based Cleanup
- **Default**: Keeps the **10 most recent** tournaments per user
- **Purpose**: Prevents high-activity users from accumulating excessive records
- **Configurable**: Can be adjusted via task configuration

## Automatic Cleanup

### Built-in Task Configuration

The cleanup task is **automatically enabled** as a built-in task. No setup required!

- **Task ID**: `cleanup_tournament_usage`
- **Frequency**: Daily at 3 AM UTC
- **Task Type**: `CLEANUP_TOURNAMENT_USAGE`
- **Scope**: Global (runs for all users/organizations)
- **Default Configuration**:
  ```json
  {
    "days_to_keep": 90,
    "keep_per_user": 10,
    "cleanup_strategy": "both"
  }
  ```

### How It Works

1. **Application startup**: Built-in tasks are loaded from `application/services/builtin_tasks.py`
2. **Task scheduler**: Checks built-in tasks alongside database tasks
3. **Execution**: Runs daily at the scheduled time
4. **Logging**: All activity is logged for monitoring

### Verifying the Task

Built-in tasks appear in the task list but are marked as `[Built-in]`:

1. Log in as an admin
2. Navigate to the Admin panel
3. View Scheduled Tasks
4. Look for "Tournament Usage Cleanup [Built-in]"

**Note**: Built-in tasks cannot be edited or deleted through the UI. To modify them, update the code in `application/services/builtin_tasks.py`.

## Modifying Built-in Task Configuration

To change the cleanup task configuration:

1. Edit `application/services/builtin_tasks.py`
2. Modify the `cleanup_tournament_usage` task definition:
   ```python
   'cleanup_tournament_usage': BuiltInTask(
       task_id='cleanup_tournament_usage',
       name='Tournament Usage Cleanup',
       # ... other fields ...
       cron_expression='0 2 * * *',  # Change time (e.g., 2 AM instead of 3 AM)
       task_config={
           'days_to_keep': 60,        # Keep last 60 days
           'keep_per_user': 15,       # Keep 15 per user
           'cleanup_strategy': 'both',
       },
       is_active=True,                # Or False to disable
   ),
   ```
3. Restart the application

## Disabling the Built-in Cleanup Task

To disable the built-in cleanup task:

1. Edit `application/services/builtin_tasks.py`
2. Set `is_active=False` in the task definition
3. Restart the application

Alternatively, create a custom database task with your preferred configuration.

## Manual Cleanup

You can also trigger cleanup manually through the service layer:

### Python/Service Example

```python
from application.services.tournament_usage_service import TournamentUsageService

usage_service = TournamentUsageService()

# Clean up entries older than 90 days
deleted_count = await usage_service.cleanup_old_usage(days_to_keep=90)
print(f"Removed {deleted_count} old entries")

# Clean up excess entries per user (keep 10 most recent)
deleted_count = await usage_service.cleanup_excess_usage(keep_per_user=10)
print(f"Removed {deleted_count} excess entries")
```

## Configuration Options

### Cleanup Strategy

The `cleanup_strategy` config option supports three values:

- **`"age"`**: Only clean up entries older than `days_to_keep`
- **`"count"`**: Only clean up excess entries per user beyond `keep_per_user`
- **`"both"`** (default): Apply both age and count-based cleanup

### Adjusting Retention Policies

To modify the retention policies, update the scheduled task configuration:

1. Navigate to Admin → Scheduled Tasks
2. Edit "Daily Tournament Usage Cleanup"
3. Update the `task_config` JSON:
   ```json
   {
     "days_to_keep": 60,        // Keep last 60 days instead of 90
     "keep_per_user": 15,       // Keep 15 per user instead of 10
     "cleanup_strategy": "both"
   }
   ```
4. Save changes

## Database Impact

### Expected Growth Rate

Assuming:
- 100 active users
- Each user accesses 3 tournaments per week
- No cleanup

**Annual growth**: ~15,600 records (100 users × 3 tournaments/week × 52 weeks)

### With Cleanup Enabled

With default settings (90 days, 10 per user):
- **Maximum records**: ~1,000 (100 users × 10 tournaments max)
- **Steady state**: Table size remains constant
- **Disk space**: Minimal (~100 KB for 1,000 records)

## Monitoring

### Log Messages

The cleanup task logs its activity:

```
INFO: Starting tournament usage cleanup task: Daily Tournament Usage Cleanup
INFO: Cleaned up 23 entries older than 90 days
INFO: Cleaned up 12 excess entries (keeping 10 per user)
INFO: Tournament usage cleanup completed: 35 total entries removed (strategy: both)
```

### Metrics to Monitor

- **Cleanup frequency**: Should run daily
- **Records deleted**: Track deletion counts over time
- **Table size**: Monitor growth trends
- **Task failures**: Check for errors in logs

## Troubleshooting

### Task Not Running

1. **Check if task exists**:
   ```bash
   poetry run python tools/setup_tournament_usage_cleanup.py
   ```

2. **Verify task is active**:
   - Admin panel → Scheduled Tasks
   - Ensure "Daily Tournament Usage Cleanup" is active

3. **Check scheduler is running**:
   - Look for "Task scheduler started" in application logs

### Excessive Deletions

If too many records are being deleted:
- Increase `days_to_keep` (e.g., 120 or 180 days)
- Increase `keep_per_user` (e.g., 15 or 20)
- Consider changing strategy to `"count"` only

### Insufficient Cleanup

If table is still growing:
- Decrease `days_to_keep` (e.g., 60 or 30 days)
- Decrease `keep_per_user` (e.g., 5)
- Ensure task is running (check logs)
- Manually trigger cleanup to catch up

## API

### Service Methods

#### `cleanup_old_usage(days_to_keep: int = 90) -> int`

Remove entries older than specified days.

**Parameters**:
- `days_to_keep`: Number of days to retain (default: 90)

**Returns**: Number of records deleted

#### `cleanup_excess_usage(keep_per_user: int = 10) -> int`

Remove excess entries per user, keeping only most recent N.

**Parameters**:
- `keep_per_user`: Number of entries to keep per user (default: 10)

**Returns**: Number of records deleted

### Repository Methods

See `application/repositories/tournament_usage_repository.py` for lower-level cleanup methods.

## Best Practices

1. **Don't disable the cleanup task** unless you have a specific reason
2. **Monitor table growth** in production environments
3. **Adjust retention policies** based on usage patterns
4. **Test configuration changes** in a staging environment first
5. **Keep retention periods reasonable** (30-180 days is typical)

## Migration Considerations

If you need to apply cleanup to an existing database with accumulated data:

```bash
# First, run the setup to create the task
poetry run python tools/setup_tournament_usage_cleanup.py

# Then manually trigger an initial cleanup via Python:
poetry run python -c "
import asyncio
from database import init_db, close_db
from application.services.tournament_usage_service import TournamentUsageService

async def cleanup():
    await init_db()
    service = TournamentUsageService()
    age_deleted = await service.cleanup_old_usage(90)
    count_deleted = await service.cleanup_excess_usage(10)
    print(f'Cleaned up {age_deleted + count_deleted} total entries')
    await close_db()

asyncio.run(cleanup())
"
```

This ensures old data is cleaned up immediately. The built-in task maintains it going forward.

## Creating Custom Database Tasks

If you need organization-specific cleanup schedules or different retention policies:

1. Navigate to Admin → Scheduled Tasks
2. Click "Create Task"
3. Select task type: `CLEANUP_TOURNAMENT_USAGE`
4. Configure schedule and parameters
5. The custom task will run alongside the built-in global task

## Built-in vs Database Tasks

| Feature | Built-in Tasks | Database Tasks |
|---------|---------------|----------------|
| Scope | Global only | Per-organization or global (admin only) |
| Configuration | Code (requires restart) | UI/API (immediate) |
| Persistence | In-memory (loaded at startup) | Database |
| Visibility | Read-only in UI | Full CRUD in UI |
| Use Case | System-level automation | Organization-specific automation |

**When to use built-in tasks:**
- System-wide maintenance (like cleanup)
- Tasks that should always run
- Tasks that don't need runtime configuration

**When to use database tasks:**
- Organization-specific schedules
- Tasks that need frequent changes
- Tasks created by admins/users
