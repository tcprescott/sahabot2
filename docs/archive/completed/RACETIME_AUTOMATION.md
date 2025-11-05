# RaceTime.gg Tournament Automation

## Overview

SahaBot2 can automatically create and manage RaceTime.gg race rooms for tournament matches. This feature eliminates the manual work of creating rooms, inviting players, and coordinating match times.

**IMPORTANT**: This implementation is based on the original SahasrahBot, which used a **forked version of racetime-bot** (https://github.com/tcprescott/racetime-bot) that added custom methods not present in the upstream library. See the "Implementation Notes" section below for details.

## Key Features

- **Automatic Room Creation**: Rooms are automatically created before scheduled matches
- **Player Invitations**: Players with linked RaceTime accounts are automatically invited
- **Configurable Timing**: Control when rooms open relative to match time
- **Optional Enforcement**: Require players to link RaceTime accounts before scheduling
- **Event Notifications**: Discord notifications when rooms are created
- **Manual Override**: Moderators can manually create rooms if needed

## Architecture

The RaceTime automation system consists of several components:

### Database Models

**Tournament Fields:**
- `racetime_bot` (FK): The RaceTime bot to use for this tournament
- `racetime_auto_create_rooms` (bool): Enable automatic room creation
- `room_open_minutes_before` (int): How many minutes before match to open room (default: 60)
- `require_racetime_link` (bool): Require all players to have RaceTime linked
- `racetime_default_goal` (string): Default goal text for race rooms

**Match Fields:**
- `racetime_room_slug` (string): The created room slug (e.g., "alttpr/cool-doge-1234")
- `racetime_goal` (string): Override default tournament goal for this match
- `racetime_invitational` (bool): Whether room is invite-only (default: true)
- `racetime_auto_create` (bool): Whether to auto-create room for this match (default: true)

### Services

**RacetimeRoomService** (`application/services/racetime_room_service.py`):
- `create_race_room_for_match()`: Create a race room for a match
- `send_room_message()`: Send messages to race rooms
- `should_create_room_for_match()`: Check if room should be created

**Scheduled Task Handler** (`application/services/task_handlers/racetime_open_room_handler.py`):
- Runs periodically (every 5 minutes recommended)
- Queries for matches needing rooms opened
- Creates rooms and invites players
- Emits events for notifications

### RaceTime Client Extensions

The RaceTime bot client (`racetime/client.py`) includes methods for:
- `create_race_room()`: Create a new race room
- `invite_user_to_race()`: Invite a player to a room
- `send_race_message()`: Send messages to race rooms

### Events

**RacetimeRoomCreatedEvent**: Emitted when a room is created
- Triggers Discord notifications
- Records audit logs
- Contains room URL, player count, etc.

**RacetimeRoomOpenedEvent**: Emitted when manually opened
- Similar to created event but for manual actions

## Setup Guide

### Prerequisites

1. **RaceTime Bot Configuration**:
   - Create an OAuth2 application on your RaceTime instance
   - Configure bot credentials in Admin > RaceTime Bots
   - Assign bot to your organization

2. **Player Requirements**:
   - Players must link their RaceTime accounts via User Profile
   - Use OAuth flow to connect Discord account to RaceTime

### Configuring Tournaments

1. **Navigate to Tournament Settings** (Organization Admin > Tournament > Settings)

2. **RaceTime Configuration Section**:
   - **RaceTime Bot**: Select the bot to use (must be assigned to organization)
   - **Auto-Create Rooms**: Enable automatic room creation
   - **Room Open Time**: Set how long before match to open room (30-120 minutes)
   - **Require RaceTime Link**: Enforce that all players have RaceTime linked
   - **Default Goal**: Set the default race goal text (e.g., "Beat the game - Tournament")

3. **Save Settings**

### Creating a Scheduled Task

The automatic room creation requires a scheduled task to be running:

1. **Navigate to Organization Admin > Scheduled Tasks**

2. **Create New Task**:
   - **Name**: "Auto-Create Race Rooms"
   - **Type**: RACETIME_OPEN_ROOM (built-in)
   - **Schedule**: INTERVAL
   - **Interval**: 300 seconds (5 minutes)
   - **Active**: Yes
   - **Configuration**: {} (empty - task checks all tournaments)

3. **Save and Activate**

The task will run every 5 minutes and check all tournaments in your organization for matches that need rooms opened.

## User Workflow

### For Players

1. **Link RaceTime Account** (if required by tournament):
   - Go to User Profile
   - Click "Link RaceTime Account"
   - Authorize via OAuth
   - Confirmation shown when linked

2. **Schedule Matches**:
   - Schedule as normal via tournament interface
   - If RaceTime linking is required and you're not linked, you'll see an error

3. **Receive Notifications**:
   - Discord notification when room is created
   - Notification includes room URL and scheduled time
   - Automatic invitation to the race room on RaceTime.gg

4. **Join Race**:
   - Click room URL in notification or check RaceTime.gg
   - Room is already configured and you're invited
   - Ready when race starts

### For Tournament Organizers

**Automatic Mode** (Recommended):
1. Configure tournament settings (see above)
2. Create scheduled task (see above)
3. Rooms are automatically created before matches
4. Monitor Discord notifications

**Manual Mode**:
1. Disable auto-create on tournament or specific matches
2. Use "Open Room" button on match detail page
3. Room is created immediately
4. Players are invited

## How It Works

### Automatic Room Creation Flow

1. **Scheduled Task Execution** (every 5 minutes):
   ```
   Task runs → Queries active tournaments with auto-create enabled
   → For each tournament, finds matches in the time window
   → Checks if room should be created
   → Creates room and invites players
   → Emits event for notifications
   ```

2. **Time Window Calculation**:
   - Match scheduled at: `2024-11-05 20:00 UTC`
   - Room open time: `60 minutes before`
   - Room creation window: `2024-11-05 19:00 - 19:05 UTC`
   - Task runs at `19:03` → Room is created

3. **Player Invitation**:
   - Query match players
   - Filter players with `racetime_id` linked
   - Invite each player to the room
   - Log invitation results

4. **Event Emission**:
   - Create `RacetimeRoomCreatedEvent`
   - Include room URL, player count, tournament info
   - Event bus distributes to handlers
   - Discord handler sends notification

### Validation Checks

Before creating a room, the system validates:

- ✅ Tournament has `racetime_auto_create_rooms` enabled
- ✅ Tournament has active RaceTime bot assigned
- ✅ RaceTime bot is running and connected
- ✅ Match has `racetime_auto_create` enabled
- ✅ Match is scheduled within the time window
- ✅ Match doesn't already have a room (`racetime_room_slug` is null)
- ✅ (Optional) All players have RaceTime accounts linked

If any check fails, the room is not created and the issue is logged.

### RaceTime Account Linking

Players link their accounts via OAuth:

1. User clicks "Link RaceTime Account" in profile
2. Redirected to RaceTime OAuth authorization
3. User authorizes the application
4. Callback receives authorization code
5. Exchange code for access token
6. Fetch RaceTime user info
7. Store `racetime_id`, `racetime_name`, `racetime_access_token`
8. User can now be invited to race rooms

## Configuration Options

### Tournament-Level Settings

| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| `racetime_bot` | FK | null | RaceTime bot to use |
| `racetime_auto_create_rooms` | boolean | false | Enable automatic creation |
| `room_open_minutes_before` | integer | 60 | Minutes before match to open room |
| `require_racetime_link` | boolean | false | Require players to have RaceTime linked |
| `racetime_default_goal` | string | null | Default goal for race rooms |

### Match-Level Overrides

| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| `racetime_goal` | string | null | Override tournament default goal |
| `racetime_invitational` | boolean | true | Whether room is invite-only |
| `racetime_auto_create` | boolean | true | Enable auto-creation for this match |

### Room Creation Parameters

When creating a room, the following parameters are used:

```python
{
    "goal": match.racetime_goal or tournament.racetime_default_goal or "Beat the game",
    "invitational": match.racetime_invitational,  # true = invite-only
    "unlisted": False,  # Rooms are always listed
    "info": "<Tournament Name> - <Match Title> - Scheduled: <Time>",
    "start_delay": 15,  # Countdown seconds
    "time_limit": 24,  # Hours
    "streaming_required": True,
    "auto_start": True,
    "allow_comments": True,
    "hide_comments": True,  # Only entrants see comments
    "allow_prerace_chat": True,
    "allow_midrace_chat": True,
    "allow_non_entrant_chat": False,
    "chat_message_delay": 0,
    "team_race": False,
    "require_even_teams": False,
}
```

## Troubleshooting

### Room Not Created

**Symptoms**: Match scheduled but no room created

**Checks**:
1. Is the tournament's `racetime_auto_create_rooms` enabled?
2. Is the match's `racetime_auto_create` enabled?
3. Is there a RaceTime bot assigned to the tournament?
4. Is the bot active and running? (Check Admin > RaceTime Bots)
5. Is the scheduled task running? (Check Organization Admin > Scheduled Tasks)
6. Is the match within the time window? (Current time + `room_open_minutes_before`)
7. Check logs for errors: `grep "racetime room" /path/to/logs`

### Players Not Invited

**Symptoms**: Room created but players not invited

**Checks**:
1. Do players have RaceTime accounts linked? (Check User Profile)
2. Are the `racetime_id` values correct in the database?
3. Is the bot still connected? (Connection may have dropped)
4. Check logs for invitation errors

### "RaceTime Account Required" Error

**Symptoms**: Cannot schedule match, error about RaceTime linking

**Cause**: Tournament has `require_racetime_link` enabled but player(s) don't have RaceTime linked

**Solution**:
1. Link RaceTime account via User Profile
2. Or ask tournament organizer to disable `require_racetime_link`

### Bot Authentication Failed

**Symptoms**: Room creation fails with "auth failed" or "401 Unauthorized"

**Cause**: Bot credentials are invalid or expired

**Solution**:
1. Go to Admin > RaceTime Bots
2. Check bot status (should show "Connected")
3. If status is "Authentication Failed":
   - Verify OAuth2 client ID and secret
   - Ensure credentials match RaceTime application
   - Re-save bot configuration to retry connection

### Room Created Too Early/Late

**Symptoms**: Room opens at wrong time relative to match

**Cause**: Incorrect `room_open_minutes_before` setting

**Solution**:
1. Check tournament settings
2. Adjust `room_open_minutes_before` value (30-120 minutes recommended)
3. Note: Scheduled task runs every 5 minutes, so timing has ±5 minute variance

## Advanced Usage

### Manual Room Creation

Moderators can manually create rooms via the match detail page:

1. Navigate to match detail
2. Click "Open Race Room" button (if no room exists)
3. Room is created immediately
4. Players are invited
5. Room URL is displayed

### Custom Room Goals

Override the default goal per-match:

1. Edit match
2. Set "Race Goal" field
3. Save
4. Room will use custom goal instead of tournament default

### Disabling Auto-Create for Specific Matches

Prevent auto-creation for a match:

1. Edit match
2. Uncheck "Auto-Create Race Room"
3. Save
4. Match will be skipped by scheduled task
5. Can still manually create room

### Testing Room Creation

To test without waiting for scheduled time:

1. Create a test match scheduled 1 hour from now
2. Temporarily set tournament's `room_open_minutes_before` to 60
3. Wait for next task execution (max 5 minutes)
4. Check if room was created
5. If not, check logs for errors

## API Integration

The RaceTime automation can also be triggered via API:

### Create Room for Match

```http
POST /api/matches/{match_id}/racetime-room
Authorization: Bearer <token>
Content-Type: application/json

{
  "goal": "Beat the game - Finals",  // optional override
  "invitational": true  // optional override
}
```

Response:
```json
{
  "room_slug": "alttpr/cool-doge-1234",
  "room_url": "https://racetime.gg/alttpr/cool-doge-1234",
  "invited_players": 2,
  "goal": "Beat the game - Finals"
}
```

### Check Room Status

```http
GET /api/matches/{match_id}/racetime-room
Authorization: Bearer <token>
```

Response:
```json
{
  "has_room": true,
  "room_slug": "alttpr/cool-doge-1234",
  "room_url": "https://racetime.gg/alttpr/cool-doge-1234",
  "created_at": "2024-11-05T19:03:00Z",
  "invited_count": 2
}
```

## Best Practices

1. **Room Open Timing**:
   - Recommended: 60 minutes before match
   - Minimum: 30 minutes (gives players time to join)
   - Maximum: 120 minutes (prevents rooms from being idle too long)

2. **RaceTime Linking**:
   - Enable `require_racetime_link` for competitive tournaments
   - Disable for casual/open events to reduce friction
   - Communicate requirement clearly to players during registration

3. **Goal Text**:
   - Be specific: "Beat the game - Tournament (Solo)" vs "Beat the game"
   - Include tournament name or round info
   - Keep it concise (max ~50 characters)

4. **Scheduled Task**:
   - Run every 5 minutes for responsive room creation
   - Don't run more frequently (unnecessary load)
   - Monitor task execution logs for errors

5. **Bot Management**:
   - Test bot connection before tournament starts
   - Have backup plan if bot fails
   - Monitor bot status in admin panel

6. **Player Communication**:
   - Announce RaceTime linking requirement early
   - Provide instructions for linking accounts
   - Send reminders before tournament starts
   - Use Discord notifications for room creation

## Migration from Original SahasrahBot

If you're migrating from the original SahasrahBot tournament system:

### Key Differences

| Feature | Original SahasrahBot | SahaBot2 |
|---------|---------------------|----------|
| Schedule Source | SpeedGaming API | Internal database |
| Room Timing | Hard-coded per tournament class | Configurable per tournament |
| Player Invites | Parsed from episode data | From match player assignments |
| Bot Management | Single bot per category | Multiple bots, org-assigned |
| Task Execution | Discord bot cron task | Built-in scheduled task system |

### Migration Steps

1. **Player Data**:
   - Players must link RaceTime accounts (no automatic migration)
   - Communicate requirement to players

2. **Bot Configuration**:
   - Create RaceTime bot entries in admin panel
   - Assign to organizations

3. **Tournament Setup**:
   - Configure RaceTime settings for each tournament
   - Set appropriate `room_open_minutes_before` values

4. **Scheduled Task**:
   - Create RACETIME_OPEN_ROOM task for each organization
   - Set to run every 5 minutes

5. **Testing**:
   - Create test matches
   - Verify rooms are created at expected times
   - Test player invitations

### What's Not Migrated

- SpeedGaming schedule integration (not needed)
- Discord role-based permissions (replaced with RaceTime linking)
- Per-tournament bot handlers (use configuration instead)

## Implementation Notes

### Fork vs. Upstream racetime-bot Library

The original SahasrahBot used a forked version of racetime-bot (https://github.com/tcprescott/racetime-bot)
that added several convenience methods not present in the upstream library:

**Fork-specific Bot methods:**
- `Bot.startrace(**kwargs)` - Creates a race room via HTTP POST and returns a handler
  - Source: https://github.com/tcprescott/racetime-bot/blob/master/racetime_bot/bot.py#L285-L324
- `Bot.join_race_room(race_name, force=False)` - Joins an existing race and returns a handler
  - Source: https://github.com/tcprescott/racetime-bot/blob/master/racetime_bot/bot.py#L228-L283

**Fork-specific Handler methods:**
- `Handler.invite_user(user)` - Invites a user to the race room
  - Source: https://github.com/tcprescott/racetime-bot/blob/master/racetime_bot/handler.py#L147-L173
- `Handler.send_message(message, ...)` - Sends a message to the race room
  - Source: https://github.com/tcprescott/racetime-bot/blob/master/racetime_bot/handler.py#L191-L210

**SahaBot2's Approach:**

SahaBot2 uses the upstream racetime-bot library (v2.3.0 from PyPI) to avoid maintaining a fork.
We implement our own simplified versions of the fork-specific Bot methods in `racetime/client.py`:

1. **startrace()** - Uses direct HTTP POST to `/o/{category}/startrace` endpoint
2. **join_race_room()** - Uses custom retry logic (5 attempts, exponential backoff) to fetch race data
   and create handlers, without external dependencies

The fork-specific Handler methods (invite_user, send_message) are available in the upstream library
and work as-is.

**Additional Improvements:**

Our RacetimeBot class also creates its own `aiohttp.ClientSession` (stored in `self.http`) for
efficient HTTP connection pooling. The upstream Bot class uses `aiohttp.request()` directly without
a session, which is less efficient. Our session is created on bot startup and properly cleaned up
on shutdown.

**Switching to the Fork:**

If you prefer to use the forked library for exact parity with original SahasrahBot:

1. Update `pyproject.toml` to use the fork:
   ```toml
   racetime-bot = { git = "https://github.com/tcprescott/racetime-bot.git" }
   ```
2. Run `poetry update racetime-bot`
3. The fork-specific methods will then be available directly on the Bot class

## Future Enhancements

Potential features for future development:

- [ ] Race result tracking and automatic database updates
- [ ] Seed distribution via bot messages
- [ ] Stream helper coordination
- [ ] Automatic room closure after race completion
- [ ] Room templates for different match types
- [ ] Integration with third-party seed generators
- [ ] Post-race statistics and reporting
- [ ] Bracket automation based on race results

## Support

For issues or questions:

1. Check troubleshooting section above
2. Review logs for error messages
3. Verify configuration settings
4. Test with a simple match first
5. Contact support with logs and configuration details
