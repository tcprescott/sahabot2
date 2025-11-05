# Orphaned Discord Event Cleanup

This document describes the automated cleanup system for orphaned Discord scheduled events.

## Overview

The orphaned event cleanup system ensures that Discord scheduled events are automatically removed when they are no longer needed. This prevents cluttering Discord servers with outdated or irrelevant events.

## What are Orphaned Events?

An event is considered "orphaned" if it meets any of these criteria:

1. **Finished Matches**: The match has completed (`finished_at` is set)
2. **Disabled Tournaments**: The tournament has `scheduled_events_enabled=False`
3. **Create Disabled**: The tournament has `create_scheduled_events=False`
4. **Deleted Matches**: The match no longer exists (database FK violation)

## Cleanup Methods

### 1. Automatic Cleanup (Scheduled Task)

**Task:** `cleanup_orphaned_discord_events`

**Schedule:** Every 6 hours (at :00, :06, :12, :18)

**Process:**
1. Finds all active organizations
2. For each organization:
   - Identifies all orphaned events
   - Deletes events from Discord
   - Removes database records
3. Logs statistics (deleted, errors)

**Location:** `application/services/builtin_tasks/orphaned_events_cleanup.py`

### 2. Tournament Sync Cleanup

**Task:** `sync_discord_scheduled_events`

**Schedule:** Every hour (at :00)

**Process:**
1. Syncs events for active tournaments
2. As part of sync, cleans up orphaned events for that tournament
3. More targeted than the full cleanup task

**Location:** `application/services/builtin_tasks/scheduled_events_sync.py`

### 3. Manual Cleanup (Service Method)

**Method:** `DiscordScheduledEventService.cleanup_orphaned_events()`

**Usage:**
```python
from application.services.discord_scheduled_event_service import DiscordScheduledEventService
from models import SYSTEM_USER_ID

service = DiscordScheduledEventService()
stats = await service.cleanup_orphaned_events(
    user_id=SYSTEM_USER_ID,
    organization_id=org_id,
)

print(f"Deleted: {stats['deleted']}, Errors: {stats['errors']}")
```

**Use Cases:**
- Manual intervention when automatic cleanup fails
- One-time cleanup after bulk operations
- Testing and development

## Repository Methods

### `list_orphaned_events(organization_id)`

Returns events for finished matches.

```python
repo = DiscordScheduledEventRepository()
orphaned = await repo.list_orphaned_events(org_id)
```

### `list_events_for_disabled_tournaments(organization_id)`

Returns events for tournaments with events disabled.

```python
repo = DiscordScheduledEventRepository()
disabled = await repo.list_events_for_disabled_tournaments(org_id)
```

### `cleanup_all_orphaned_events(organization_id)`

Returns all orphaned events (finished + disabled, deduplicated).

```python
repo = DiscordScheduledEventRepository()
all_orphaned = await repo.cleanup_all_orphaned_events(org_id)
```

## Cleanup Process

For each orphaned event:

1. **Query Discord**: Fetch the event from Discord in each guild
2. **Delete from Discord**: Call `scheduled_event.delete()`
3. **Delete from Database**: Remove the `DiscordScheduledEvent` record
4. **Log Results**: Record success or errors

**Error Handling:**
- If Discord delete fails, database record is still removed
- Errors are logged but don't stop other deletions
- Statistics track both successful deletions and errors

## Multi-Tenant Isolation

All cleanup operations respect organization boundaries:

✅ **Correct:**
```python
# Only cleans up events in organization 123
await service.cleanup_orphaned_events(
    user_id=SYSTEM_USER_ID,
    organization_id=123,
)
```

❌ **Wrong:**
```python
# Don't mix organizations!
events_org1 = await repo.list_orphaned_events(org1_id)
await delete_event_for_match(org2_id, event.match_id)  # Will fail!
```

## Statistics and Logging

### Cleanup Statistics

```python
{
    'deleted': 15,      # Successfully deleted events
    'errors': 2,        # Errors encountered
}
```

### Log Messages

**Info Level:**
```
Cleaning up 15 orphaned Discord events in org 123 (user 0)
Orphaned event cleanup complete for org 123: 15 deleted, 2 errors
```

**Error Level:**
```
Error cleaning up orphaned event 456 (match 789): NotFound
```

## Testing

### Unit Tests

**File:** `tests/unit/test_orphaned_event_cleanup.py`

**Coverage:**
- Finding orphaned events (finished matches)
- Finding events for disabled tournaments
- Deduplication when event matches multiple criteria
- Tenant isolation
- Service cleanup method

### Running Tests

```bash
# All orphaned cleanup tests
pytest tests/unit/test_orphaned_event_cleanup.py -v

# Specific test
pytest tests/unit/test_orphaned_event_cleanup.py::TestOrphanedEventCleanup::test_cleanup_all_orphaned_events -v
```

## Common Scenarios

### Scenario 1: Tournament Ends

**What happens:**
1. Tournament admin marks all matches as finished
2. Next sync task (every hour) identifies orphaned events
3. Events are deleted from Discord
4. Database records are removed

**Timeline:** Within 1 hour

### Scenario 2: Tournament Disables Events

**What happens:**
1. Admin sets `scheduled_events_enabled=False`
2. Next cleanup task (every 6 hours) finds events for disabled tournament
3. All events for that tournament are deleted
4. Future matches in that tournament won't create events

**Timeline:** Within 6 hours

### Scenario 3: Match is Deleted

**What happens:**
1. Match is deleted (via UI or API)
2. `MatchDeletedEvent` is emitted
3. Event listener calls `delete_event_for_match()`
4. Event is deleted immediately (not waiting for cleanup task)

**Timeline:** Immediate

### Scenario 4: Bot Loses Permission

**What happens:**
1. Cleanup task tries to delete event
2. Discord returns 403 Forbidden
3. Error is logged
4. Database record is still removed (orphaned in DB)
5. Next cleanup attempt will skip (no DB record)

**Resolution:** Fix bot permissions, manually delete events in Discord

## Monitoring and Troubleshooting

### Check Cleanup Task Status

```python
from application.services.task_scheduler_service import TaskSchedulerService

scheduler = TaskSchedulerService()
history = await scheduler.get_task_history("cleanup_orphaned_discord_events", limit=10)

for entry in history:
    print(f"{entry.executed_at}: {entry.status} - {entry.output}")
```

### Manual Cleanup After Issue

```python
from application.services.discord_scheduled_event_service import DiscordScheduledEventService
from models import SYSTEM_USER_ID

service = DiscordScheduledEventService()

# Clean up all orphaned events for organization
stats = await service.cleanup_orphaned_events(
    user_id=SYSTEM_USER_ID,
    organization_id=your_org_id,
)

print(f"Cleanup complete: {stats}")
```

### Find Orphaned Events Without Deleting

```python
from application.repositories.discord_scheduled_event_repository import DiscordScheduledEventRepository

repo = DiscordScheduledEventRepository()
orphaned = await repo.cleanup_all_orphaned_events(org_id)

print(f"Found {len(orphaned)} orphaned events:")
for event in orphaned:
    print(f"  Event {event.scheduled_event_id} for match {event.match_id}")
```

## Configuration

### Cleanup Task Schedule

**Current:** Every 6 hours

**Location:** `application/services/builtin_tasks/orphaned_events_cleanup.py`

**Modify:**
```python
TASK_SCHEDULE = "0 */6 * * *"  # Cron format
```

**Options:**
- `"0 * * * *"` - Every hour
- `"0 */12 * * *"` - Every 12 hours
- `"0 2 * * *"` - Daily at 2 AM

### Enable/Disable Cleanup Task

```python
TASK_ENABLED = True  # Set to False to disable
```

## Best Practices

1. **Let Automation Handle It**: Don't manually delete events unless necessary
2. **Monitor Logs**: Check for recurring errors
3. **Fix Permissions**: Ensure bot has MANAGE_EVENTS in all guilds
4. **Test Changes**: Use staging environment to test tournament changes
5. **Gradual Rollout**: When disabling events, monitor the first cleanup cycle

## Performance Considerations

- **Database Queries**: Uses efficient filtering with indexes
- **Discord API**: Respects rate limits (one delete per event)
- **Batch Processing**: Processes all organizations in one task run
- **Error Isolation**: One org's errors don't affect others

## Future Enhancements

Potential improvements for the cleanup system:

1. **Batch Discord Deletes**: Delete multiple events per guild in one operation
2. **Retry Logic**: Retry failed deletions before giving up
3. **Notification**: Alert admins when cleanup encounters many errors
4. **Analytics**: Track cleanup metrics over time
5. **Selective Cleanup**: Allow cleanup of specific tournament/match ranges
