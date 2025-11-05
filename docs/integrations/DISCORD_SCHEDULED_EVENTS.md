# Discord Scheduled Events Integration

## Overview

This feature automatically creates, updates, and manages Discord's native scheduled events for tournament matches. When a match is scheduled in a tournament, a corresponding event appears in the Discord server's "Events" section, making it easy for community members to discover and track upcoming matches.

## Status

**Implementation Status:** Complete ✅

### Completed Components
- ✅ **Database Model** (`models/discord_scheduled_event.py`): Tracks mapping between matches and Discord events with status tracking
- ✅ **Tournament Configuration** (`models/match_schedule.py`): Added `create_scheduled_events`, `scheduled_events_enabled`, `discord_event_filter`, and `event_duration_hours` fields
- ✅ **Repository Layer** (`application/repositories/discord_scheduled_event_repository.py`): Full CRUD operations
- ✅ **Service Layer** (`application/services/discord_scheduled_event_service.py`): Complete business logic for event lifecycle and status management
- ✅ **Event Formatting**: Helper methods to format event names, descriptions, locations
- ✅ **Background Sync Task** (`builtin_tasks/scheduled_events_sync.py`): Hourly synchronization with automatic status updates
- ✅ **Permission Checking**: Discord bot permission validation
- ✅ **Database Migrations**: Applied migrations for all features
- ✅ **Configurable Duration**: Event duration configurable per tournament (default 2 hours)
- ✅ **Automatic Status Updates**: Events automatically transition scheduled → active → completed/cancelled

## Architecture

### Data Flow

```
Match Scheduled/Updated
    ↓
MatchScheduledEvent emitted
    ↓
Event Listener triggered
    ↓
DiscordScheduledEventService.create_event_for_match()
    ↓
Format event details (name, description, location, times)
    ↓
Check Discord bot permissions
    ↓
Call Discord API to create scheduled event
    ↓
Store mapping in DiscordScheduledEvent table
```

### Database Schema

**DiscordScheduledEvent Model:**
```python
{
    "id": int,
    "scheduled_event_id": bigint (Discord's unique ID),
    "match_id": FK to Match,
    "organization_id": FK to Organization,
    "event_slug": str (optional, e.g., "alttpr2024"),
    "discord_status": str (scheduled/active/completed/cancelled),
    "created_at": datetime,
    "updated_at": datetime
}
```

**Tournament Configuration Fields:**
```python
{
    "create_scheduled_events": bool (default False),  # Enable feature
    "scheduled_events_enabled": bool (default True),  # Master toggle
    "discord_event_filter": DiscordEventFilter enum,  # Filter events (ALL/STREAM_ONLY/NONE)
    "event_duration_minutes": int (default 120),  # Configurable event duration in minutes
}
```

### Multi-Tenancy

All operations are organization-scoped:
- Events are created in the Discord guild linked to the organization
- Repository methods require `organization_id` parameter
- Event queries filter by organization
- No cross-tenant data leakage

## Original Feature Reference

This feature is ported from the original SahasrahBot:
- **Source**: https://github.com/tcprescott/sahasrahbot/blob/main/alttprbot_discord/cogs/tournament.py#L177-L265
- **Key Method**: `update_scheduled_event()`
- **Data Model**: `ScheduledEvents` model tracked event_id → episode_id mapping

### Key Differences from Original

| Aspect | Original SahasrahBot | New SahaBot2 |
|--------|---------------------|--------------|
| **Match Source** | SpeedGaming API episodes | Internal Match model |
| **Tenant Model** | Single-instance per community | Multi-tenant with Organizations |
| **Event Trigger** | Scheduled task polling SG API | Event-driven (MatchScheduledEvent) |
| **Configuration** | Per-event-slug in TournamentConfig | Per-tournament database field |
| **Cleanup** | Deletes events not in SG schedule | Deletes events for finished matches |

## Configuration

### Per-Tournament Setup

1. **Enable Discord Events** for a tournament:
   ```python
   tournament.create_scheduled_events = True
   tournament.scheduled_events_enabled = True
   await tournament.save()
   ```

2. **Link Discord Guild** to organization (prerequisite):
   - Organization must have a Discord guild linked
   - Bot must be in the guild with "Manage Events" permission

3. **Match Requirements**:
   - Match must have `scheduled_at` datetime set
   - Match must belong to a tournament with events enabled

### Discord Bot Permissions

Required permission in Discord guild:
- **Manage Events** (`MANAGE_EVENTS` or `1 << 33`)

Without this permission, event creation will fail gracefully (logged but not blocking).

## Event Formatting

### Event Name (max 100 characters)
Format: `{TOURNAMENT_SLUG} - {MATCH_TITLE or VS_STRING}`

Examples:
- `ALTTPR2024 - Alice vs Bob`
- `CC2024 - Semifinals Match 1`

### Event Description
Format:
```
Match: {match_title or player names}
Tournament: {tournament_name}

Scheduled: {discord timestamp}
Stream: {stream_channel or TBD}
```

### Event Location
Priority order:
1. Stream channel URL if assigned: `https://twitch.tv/{channel}`
2. Multistream URL if multiple player streams known
3. `"TBD"` if no stream information available

### Event Times
- **Start Time**: Match `scheduled_at` datetime
- **End Time**: Start time + `tournament.event_duration_minutes` (configurable in minutes, default 120 = 2 hours)
- **Privacy**: Guild-only (not public)
- **Entity Type**: External (not voice channel or stage)

## Event Status Management

### Status Lifecycle

Discord events follow this status lifecycle:
1. **scheduled** - Event is created and awaiting start time
2. **active** - Event has started (automatically updated when match time arrives)
3. **completed** - Event has finished (automatically updated when match is reported)
4. **cancelled** - Event is cancelled (automatically updated when match is cancelled)

### Automatic Status Updates

The background sync task (`scheduled_events_sync.py`) runs hourly and automatically updates event statuses:

**scheduled → active:**
- Triggered when `match.scheduled_at <= current_time`
- Discord event status set to `active`
- Database record updated to `discord_status='active'`

**active → completed:**
- Triggered when match is reported/finished (`match.status in ['completed', 'reported']` or `match.winner is not None`)
- Discord event status set to `completed`
- Database record updated to `discord_status='completed'`

**any → cancelled:**
- Triggered when match is cancelled (`match.status == 'cancelled'`)
- Discord event status set to `cancelled`
- Database record updated to `discord_status='cancelled'`

### Manual Status Updates

```python
service = DiscordScheduledEventService()
db_event = await DiscordScheduledEvent.get(id=event_id)

# Update status in database and Discord
await service.update_event_status(
    db_event=db_event,
    new_status='completed'
)
```

## Configurable Event Duration

### Per-Tournament Configuration

Event duration can be configured per tournament in minutes (default 120 minutes = 2 hours):

```python
# Set custom event duration (240 minutes = 4 hours)
tournament.event_duration_minutes = 240
await tournament.save()
```

### Usage Examples

**Quick matches (60 minutes):**
```python
tournament.event_duration_minutes = 60  # 1 hour
```

**Standard short races (90 minutes):**
```python
tournament.event_duration_minutes = 90  # 1.5 hours - perfect for typical races
```

**Standard matches (120 minutes, default):**
```python
tournament.event_duration_minutes = 120  # 2 hours (default)
```

**Long matches (180 minutes):**
```python
tournament.event_duration_minutes = 180  # 3 hours
```

**Extended matches (240 minutes):**
```python
tournament.event_duration_minutes = 240  # 4 hours
```

**All-day events (480 minutes):**
```python
tournament.event_duration_minutes = 480  # 8 hours for marathon events
```

The configured duration is automatically used when creating or updating Discord events. This allows precise control over event timing, accommodating matches of any length from quick 30-minute sprints to all-day marathon races.

## API Operations

### Create Event
```python
service = DiscordScheduledEventService()
await service.create_event_for_match(
    user=current_user,
    organization_id=org_id,
    match_id=match_id,
)
```

### Update Event
```python
await service.update_event_for_match(
    user=current_user,
    organization_id=org_id,
    match_id=match_id,
)
```

### Delete Event
```python
await service.delete_event_for_match(
    user=current_user,
    organization_id=org_id,
    match_id=match_id,
)
```

### Manual Sync (Admin)
```python
await service.sync_tournament_events(
    user=admin_user,
    organization_id=org_id,
    tournament_id=tournament_id,
)
```

## Event Listeners Integration

### MatchScheduledEvent
When a match is scheduled or rescheduled, create/update Discord event:
```python
@EventBus.on(MatchScheduledEvent, priority=EventPriority.NORMAL)
async def create_discord_event_for_match(event: MatchScheduledEvent):
    service = DiscordScheduledEventService()
    await service.create_event_for_match(
        user_id=event.user_id,
        organization_id=event.organization_id,
        match_id=event.entity_id,
    )
```

### MatchUpdatedEvent
When match details change (title, time, stream), update Discord event:
```python
@EventBus.on(MatchUpdatedEvent, priority=EventPriority.NORMAL)
async def update_discord_event_for_match(event: MatchUpdatedEvent):
    # Only update if relevant fields changed
    if 'scheduled_at' in event.changed_fields or 'title' in event.changed_fields:
        service = DiscordScheduledEventService()
        await service.update_event_for_match(...)
```

### MatchDeletedEvent
When a match is deleted, remove Discord event:
```python
@EventBus.on(MatchDeletedEvent, priority=EventPriority.NORMAL)
async def delete_discord_event_for_match(event: MatchDeletedEvent):
    service = DiscordScheduledEventService()
    await service.delete_event_for_match(...)
```

## Background Sync Task

**Purpose**: Ensure all upcoming matches have corresponding Discord events and status is kept up-to-date.

**Schedule**: Runs every hour

**Scope**: All active tournaments with `create_scheduled_events=True`

**Logic**:
1. Sync events for each tournament (create/update/delete)
2. Auto-update event statuses based on match timing:
   - Activate events for matches that have started
   - Complete events for matches that are finished
   - Cancel events for cancelled matches
3. Log statistics about operations performed

**Implementation Location**: `application/services/builtin_tasks/scheduled_events_sync.py`

**Statistics Tracked:**
- Events created
- Events updated
- Events deleted
- Events activated (scheduled → active)
- Events completed (active → completed)
- Events cancelled (any → cancelled)
- Errors encountered

## Error Handling

### Permission Errors
```python
try:
    event = await guild.create_scheduled_event(...)
except discord.Forbidden:
    logger.error("Bot lacks MANAGE_EVENTS permission in guild %s", guild.id)
    # Return gracefully, don't raise
    return None
```

### Not Found Errors
```python
try:
    event = await guild.fetch_scheduled_event(event_id)
except discord.NotFound:
    logger.warning("Discord event %s no longer exists", event_id)
    # Clean up database record
    await repo.delete_by_event_id(org_id, event_id)
```

### Rate Limiting
Discord API has rate limits on event creation. The sync task should:
- Batch operations
- Add delays between calls if needed
- Respect `Retry-After` headers

## UI Integration

### Tournament Admin Page
Location: `views/admin/admin_tournaments.py`

**Create/Edit Tournament Dialog:**
- Checkbox: "Enable Discord Scheduled Events"
- Help text: "Automatically create Discord events for scheduled matches (requires Discord guild link and bot permissions)"

**Tournament Details View:**
- Show sync status and last sync time
- Button: "Sync Events Now" (manual trigger for admins)
- Display count of upcoming events

### Organization Settings
- Link to Discord bot permission checker
- Warning if bot lacks MANAGE_EVENTS permission

## Testing Strategy

### Unit Tests
- Repository CRUD operations
- Event formatting (name length, description, location logic)
- Permission checking

### Integration Tests
- Event creation flow (match scheduled → Discord event created)
- Event update flow (match rescheduled → Discord event updated)
- Event deletion flow (match deleted → Discord event deleted)
- Sync task (mock upcoming matches, verify events created)

### Mock Discord API
Use mock Discord client to test API interactions without hitting live Discord.

## Troubleshooting

### Events Not Creating

**Check:**
1. Tournament has `create_scheduled_events=True`
2. Organization has Discord guild linked
3. Bot has MANAGE_EVENTS permission in guild
4. Match has `scheduled_at` set
5. Check logs for API errors

**Logs to inspect:**
```bash
grep "Discord scheduled event" logs/app.log
```

### Permission Denied

**Fix:**
1. Go to Discord Developer Portal
2. Select your bot application
3. Ensure "Manage Events" is checked in OAuth2 scopes
4. Regenerate bot invite link with new permissions
5. Re-invite bot to server (kick and re-add, or use new invite)

### Events Not Updating

**Check:**
- Background sync task is running (`ScheduledTask` table should have `discord_events_sync`)
- Match updates are emitting `MatchUpdatedEvent`
- Event listener is registered

### Orphaned Events

**Manual Cleanup:**
```python
repo = DiscordScheduledEventRepository()
orphaned = await repo.list_orphaned_events(org_id)
for event in orphaned:
    await service.delete_event_for_match(org_id, event.match_id)
```

## Future Enhancements

- [ ] Support for multi-day tournaments (event series)
- [ ] Event description templates per tournament
- [ ] Notification when event is about to start (Discord's built-in notifications)
- [ ] Integration with Discord's event RSVP system
- [ ] Rich embed images for events (tournament logos)

## References

- **Original Implementation**: [SahasrahBot tournament.py](https://github.com/tcprescott/sahasrahbot/blob/main/alttprbot_discord/cogs/tournament.py#L177-L265)
- **Discord API Docs**: [Scheduled Events](https://discord.com/developers/docs/resources/guild-scheduled-event)
- **Discord.py Docs**: [ScheduledEvent](https://discordpy.readthedocs.io/en/stable/api.html#discord.ScheduledEvent)

## Migration Checklist

- [ ] Create database migration
- [ ] Update database initialization in `database.py`
- [ ] Implement service layer
- [ ] Add event listeners
- [ ] Create background sync task
- [ ] Add UI controls
- [ ] Update admin documentation
- [ ] Test on staging environment
- [ ] Deploy to production
- [ ] Monitor logs for errors
- [ ] Collect user feedback
