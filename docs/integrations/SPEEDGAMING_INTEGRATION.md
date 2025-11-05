# SpeedGaming API Integration

## Overview

SahaBot2 integrates with [SpeedGaming.org](https://speedgaming.org) to automatically import tournament match schedules. This enables automated tournament workflows by syncing SpeedGaming episodes as matches in the application.

SpeedGaming is the primary platform for ALTTPR/randomizer tournaments and restreams, hosting 20-30 tournaments per year.

## Architecture

### ETL-Based Import

The integration uses an **ETL (Extract, Transform, Load)** approach:

- **Extract**: Fetch episode data from SpeedGaming API every 5 minutes
- **Transform**: Map episode data to Match, MatchPlayers, and Crew models
- **Load**: Create/update database records

### Read-Only Schedule

SpeedGaming remains the **source of truth** for match scheduling:
- Matches imported from SpeedGaming are linked via `speedgaming_episode_id`
- The application does not push changes back to SpeedGaming
- Schedule updates happen automatically via periodic import

### Model Reuse

Instead of creating SpeedGaming-specific models, the integration **reuses existing models**:
- `Match` - Stores imported episodes (linked via `speedgaming_episode_id`)
- `MatchPlayers` - Stores episode players
- `Crew` - Stores commentators and trackers
- `User` - Maps SpeedGaming players/crew to application users

## Configuration

### Enable SpeedGaming Integration

To enable SpeedGaming integration for a tournament:

1. **Enable Integration**: Set `speedgaming_enabled = True` on the Tournament
2. **Configure Event Slug**: Set `speedgaming_event_slug` to the SpeedGaming event identifier (e.g., `"alttprleague"`)

```python
tournament = await tournament_service.create_tournament(
    user=current_user,
    organization_id=org_id,
    name="ALTTPR League",
    speedgaming_enabled=True,
    speedgaming_event_slug="alttprleague",
    # ... other settings
)
```

### Automatic Import

The built-in task `speedgaming_import` runs **every 5 minutes** to:
1. Find all tournaments with `speedgaming_enabled=True`
2. Fetch upcoming episodes from SpeedGaming API
3. Import new episodes as matches
4. Skip episodes that have already been imported

## Player & Crew Matching

### Discord ID Matching

The integration attempts to match SpeedGaming players/crew to existing application users:

1. **Match by Discord ID**: If the SpeedGaming data includes a `discordId`, find the existing user
2. **Ensure Organization Membership**: Add matched users to the organization if not already a member

### Placeholder Users

When a Discord ID is **not available** in SpeedGaming data, the integration creates a **placeholder user**:

- **Username**: `sg_{player_id}` or `sg_crew_{crew_id}` (unique identifier based on SpeedGaming ID)
- **Marked as Placeholder**: `is_placeholder = True` flag for tracking
- **Discord ID**: Set to `0` (invalid ID indicating placeholder)
- **Organization Membership**: Automatically added to the tournament's organization

Placeholder users can be **upgraded** to real users when:
- The person authenticates with Discord
- An admin manually links the placeholder to a real account
- SpeedGaming data is updated with a Discord ID

### Example: Player Import Flow

```
SpeedGaming Episode Player:
{
  "id": 11111,
  "displayName": "synack",
  "discordId": "123456789012345678",  // Available
  "discordTag": "Synack#1337"
}

→ Find User with discord_id=123456789012345678
→ User found: Add to organization if needed
→ Create MatchPlayers record linking User to Match
```

```
SpeedGaming Episode Player (No Discord ID):
{
  "id": 11111,
  "displayName": "synack",
  "discordId": "",  // Not available
  "discordTag": "Synack#1337"
}

→ Check for placeholder user with username="sg_11111"
→ If not found, create User:
   - discord_id=0
   - discord_username="sg_11111"
   - is_placeholder=True
→ Add to organization
→ Create MatchPlayers record linking placeholder User to Match
```

## Data Models

### Database Schema Changes

```python
# Tournament model additions
class Tournament(Model):
    speedgaming_enabled = fields.BooleanField(default=False)
    speedgaming_event_slug = fields.CharField(max_length=255, null=True)

# Match model additions
class Match(Model):
    speedgaming_episode_id = fields.IntField(null=True, unique=True)

# User model additions
class User(Model):
    is_placeholder = fields.BooleanField(default=False)
```

### SpeedGaming Data Classes

The integration uses dataclasses to represent SpeedGaming API responses:

- `SpeedGamingPlayer` - Player data with Discord ID matching
- `SpeedGamingCrewMember` - Commentator/tracker data
- `SpeedGamingMatch` - Match within an episode
- `SpeedGamingEvent` - Tournament/event information
- `SpeedGamingChannel` - Broadcast channel information
- `SpeedGamingEpisode` - Complete episode data

## API Endpoints

### SpeedGaming API

Base URL: `https://speedgaming.org/api`

- **GET /episode/{episode_id}** - Fetch episode details
- **GET /schedule?event={event_slug}** - Fetch upcoming episodes for an event

### Service Methods

```python
from application.services.speedgaming_service import SpeedGamingService

service = SpeedGamingService()

# Fetch single episode
episode = await service.get_episode(episode_id=12345)

# Fetch upcoming episodes for event
episodes = await service.get_upcoming_episodes_by_event(
    event_slug="alttprleague",
    limit=100
)
```

### ETL Service

```python
from application.services.speedgaming_etl_service import SpeedGamingETLService

etl_service = SpeedGamingETLService()

# Import single episode
match = await etl_service.import_episode(tournament, episode)

# Import all episodes for a tournament
imported, skipped = await etl_service.import_episodes_for_tournament(tournament_id)

# Import for all enabled tournaments (used by scheduled task)
total_imported, total_skipped = await etl_service.import_all_enabled_tournaments()
```

## Scheduled Task

### Task Configuration

**Task ID**: `speedgaming_import`
**Task Type**: `SPEEDGAMING_IMPORT`
**Schedule**: Every 5 minutes (300 seconds)
**Scope**: Global (not organization-specific)

The task is registered as a built-in task in `application/services/builtin_tasks.py`:

```python
'speedgaming_import': BuiltInTask(
    task_id='speedgaming_import',
    name='SpeedGaming Episode Import',
    description='Imports upcoming SpeedGaming episodes as matches for tournaments with SpeedGaming integration enabled',
    task_type=TaskType.SPEEDGAMING_IMPORT,
    schedule_type=ScheduleType.INTERVAL,
    is_global=True,
    interval_seconds=300,  # Every 5 minutes
    task_config={},
    is_active=True,
)
```

### Task Handler

The task handler in `application/services/task_handlers.py` calls the ETL service:

```python
async def handle_speedgaming_import(task: ScheduledTask) -> None:
    """Import SpeedGaming episodes into matches."""
    etl_service = SpeedGamingETLService()
    imported, skipped = await etl_service.import_all_enabled_tournaments()
    logger.info("Completed SpeedGaming import: %s imported, %s skipped", imported, skipped)
```

## Workflow Example

### 1. Configure Tournament

```python
# Admin enables SpeedGaming integration
tournament = await tournament_service.update_tournament(
    user=admin_user,
    organization_id=1,
    tournament_id=5,
    speedgaming_enabled=True,
    speedgaming_event_slug="alttprleague",
)
```

### 2. Scheduled Import (Every 5 Minutes)

```
1. Task runs: handle_speedgaming_import()
2. ETL service finds tournaments with speedgaming_enabled=True
3. For each tournament:
   a. Fetch episodes from SpeedGaming API
   b. For each episode:
      - Check if already imported (by speedgaming_episode_id)
      - If new, import:
        * Create Match record
        * Match/create players → Create MatchPlayers
        * Match/create crew → Create Crew
4. Log results
```

### 3. Match Created

```
Match:
  tournament_id: 5
  speedgaming_episode_id: 12345
  title: "Standard - Week 1"
  scheduled_at: 2022-11-06 18:00:00+00:00
  
MatchPlayers:
  - User(id=123, discord_id=123456789)  # Matched user
  - User(id=456, discord_username="sg_11111", is_placeholder=True)  # Placeholder

Crew (Commentators):
  - User(id=789, discord_id=987654321)  # Matched commentator
```

## Integration Points

### Existing Features

SpeedGaming-imported matches integrate with:

1. **RaceTime.gg Integration**: Auto-create race rooms at scheduled time (if enabled)
2. **Discord Scheduled Events**: Create Discord events for matches (if enabled)
3. **Tournament Dashboard**: Display matches in organization/tournament views
4. **Player Notifications**: Notify players via Discord DM when matches are scheduled

### Match Lifecycle

```
[SpeedGaming Episode Created]
        ↓
[Imported as Match] (via scheduled task)
        ↓
[Race Room Opened] (if racetime_auto_create=True)
        ↓
[Players Notified] (via Discord notifications)
        ↓
[Match Completed]
        ↓
[Results Tracked] (manual or automatic from RaceTime.gg)
```

## Limitations

### Current Scope

- **One-way sync**: SpeedGaming → SahaBot2 (no push back)
- **Episode-level import**: Imports entire episodes, not individual match updates
- **Deduplication by episode ID**: Once imported, episodes are not re-imported
- **No automatic updates**: If an episode changes on SpeedGaming, it won't update in the app

### Future Enhancements

Potential future improvements:
- [ ] Update detection (re-fetch modified episodes)
- [ ] Match result export to SpeedGaming
- [ ] Player stream URL sync
- [ ] Automated seed generation based on SpeedGaming match settings
- [ ] Commentary channel notifications
- [ ] Scheduling needs tracking (commentator/tracker availability)

## Error Handling

### API Errors

- **Network failures**: Logged and skipped (retry on next task run)
- **HTTP errors**: Logged with status code and error details
- **Malformed data**: Logged and skipped (episode not imported)

### Data Validation

- **Missing players**: Episodes with no players are skipped
- **Invalid Discord IDs**: Handled gracefully by creating placeholder users
- **Duplicate episodes**: Checked via `speedgaming_episode_id` unique constraint

### Logging

All operations are logged with appropriate levels:
- **INFO**: Normal import operations, matched users, created records
- **WARNING**: Missing data, skipped episodes
- **ERROR**: API failures, unexpected errors

Example log output:
```
INFO: Fetched 5 upcoming episodes for event 'alttprleague'
INFO: Matched player 'synack' to existing user 123
INFO: Created placeholder user 456 for SpeedGaming player 'John' (ID: 11111)
INFO: Created match 789 for episode 12345
INFO: Added player 123 to match 789
INFO: Added commentator 234 to match 789
INFO: Completed import for tournament 5: 1 imported, 0 skipped
```

## Testing

### Unit Tests

Located in `tests/integration/test_speedgaming_service.py`:

- Data class parsing from API responses
- Discord ID matching logic
- Placeholder user creation

### Integration Tests

Manual testing checklist:
1. Enable SpeedGaming on tournament
2. Verify scheduled task runs
3. Check matches are created
4. Verify players are matched/created
5. Confirm crew members are imported
6. Test with missing Discord IDs
7. Verify deduplication works

## Troubleshooting

### Matches Not Importing

1. **Check tournament configuration**:
   - `speedgaming_enabled = True`
   - `speedgaming_event_slug` is set and correct
   - Tournament is active (`is_active = True`)

2. **Check task scheduler**:
   - Task is enabled: `speedgaming_import.is_active = True`
   - Check logs for task execution

3. **Check API connectivity**:
   - Test SpeedGaming API: `curl https://speedgaming.org/api/schedule?event=alttprleague`

### Duplicate Players

If players appear multiple times:
- Check SpeedGaming data for duplicate player entries
- Verify Discord ID matching is working correctly
- Look for placeholder users that should be matched to real users

### Missing Discord IDs

If many placeholder users are created:
- Coordinate with SpeedGaming to add Discord IDs to player profiles
- Manually link placeholder users to real users via admin interface (future feature)

## References

- **SpeedGaming**: https://speedgaming.org
- **Implementation Files**:
  - `application/services/speedgaming_service.py` - API client
  - `application/services/speedgaming_etl_service.py` - ETL logic
  - `application/services/task_handlers.py` - Scheduled task handler
  - `models/match_schedule.py` - Tournament and Match models
  - `models/user.py` - User model with placeholder flag
