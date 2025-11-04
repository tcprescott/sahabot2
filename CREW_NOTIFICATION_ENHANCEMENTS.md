# Enhanced Crew Approval Notifications

## Overview
Crew approval notifications now include comprehensive match details to help crew members prepare for their assigned matches.

## Implementation Date
2025-11-03

## What's New

### Additional Match Information
When you receive a crew approval notification, it now includes:

1. **Tournament Name** - Which tournament the match is part of
2. **Stream Channel** - Where the match will be streamed (if assigned)
3. **Player Names** - Who's competing in the match
4. **Match ID** - For reference
5. **Role** - Your assigned crew role (Tracker, Commentator, etc.)
6. **Approver** - Who approved or assigned you

## Example Notifications

### Manual Approval (User signed up and was approved)
```
✅ Crew Signup Approved

Your Tracker signup for ALTTPR Tournament S5 has been approved!

Role: Tracker
Match ID: 42
Stream Channel: #speedruns-1
Players: Alice, Bob
Approved By: TournamentAdmin

Check the match schedule for full details
```

### Auto-Approval (Admin added crew directly)
```
🎬 Crew Role Assigned

You've been assigned as Commentator for a match in ALTTPR Tournament S5!

Role: Commentator
Match ID: 42
Stream Channel: #speedruns-1
Players: Charlie, Dana, Eve
Assigned By: TournamentOrganizer

Check the match schedule for full details
```

### Match with Many Players
When there are more than 4 players, the list is truncated:
```
Players: Alice, Bob, Charlie, +3 more
```

### Match Without Stream Channel
If no stream channel is assigned, that field is omitted:
```
Role: Tracker
Match ID: 42
Players: Alice, Bob
Approved By: Admin
```

## Implementation Details

### Changes Made

#### 1. Updated Event Listeners (`application/events/listeners.py`)
Both `notify_crew_approved` and `notify_crew_added_auto_approved` now:
- Fetch the match details using `Match.filter(id=match_id).prefetch_related('tournament', 'participants__user')`
- Extract tournament name from `match.tournament.name`
- Extract stream channel from `match.stream_channel`
- Extract player names from `match.participants` (list of usernames)
- Include all this data in the `event_data` dictionary

**Event Data Structure:**
```python
event_data = {
    "match_id": int,
    "crew_id": int,
    "role": str,
    "approved_by": str or "added_by": str,
    "auto_approved": bool,
    "tournament_name": str or None,
    "stream_channel": str or None,
    "players": list[str],  # List of player usernames
}
```

#### 2. Enhanced Discord Handler (`discord_handler.py`)
The `_send_crew_approved` method now:
- Includes tournament name in the description if available
- Adds stream channel as a field (if present)
- Lists players (with smart truncation for large matches)
- Reorders fields for better visual hierarchy:
  1. Role & Match ID (inline, side-by-side)
  2. Stream Channel (full width)
  3. Players (full width, truncated if many)
  4. Approver/Assigner (full width)

**Smart Player Display:**
- 1-4 players: Show all names
- 5+ players: Show first 3 + count of remaining (e.g., "Alice, Bob, Charlie, +5 more")

## Database Queries

The listeners now perform efficient database queries with prefetching:

```python
match = await Match.filter(id=event.match_id).prefetch_related(
    'tournament',           # Fetch related tournament
    'participants__user'    # Fetch participants and their users
).first()
```

This uses Tortoise ORM's `prefetch_related` to avoid N+1 query problems.

## Benefits

1. **Better Context**: Crew members immediately know what match they're working on
2. **Stream Preparation**: Stream channel info helps crew coordinate with streamers
3. **Player Recognition**: Knowing who's playing helps crew prepare appropriately
4. **Tournament Awareness**: Understanding tournament context aids in following guidelines
5. **Single Source**: All relevant info in one notification

## Testing Recommendations

1. **Approve crew manually**:
   - Create a match with tournament, stream channel, and players
   - Have a user sign up for crew
   - Approve them
   - Verify notification includes all details

2. **Auto-approve crew**:
   - As admin, directly assign crew to a match
   - Verify notification shows "Crew Role Assigned" with details

3. **Edge cases**:
   - Match without tournament → Should still work, omit tournament name
   - Match without stream channel → Should omit stream channel field
   - Match with many players (10+) → Should truncate player list
   - Match with no players → Should omit players field

4. **Multiple organizations**:
   - Verify global subscriptions receive notifications from all orgs
   - Verify org-scoped subscriptions only receive from their org

## Related Files

- `application/events/listeners.py` - Fetch match details and queue notifications
- `application/services/notification_handlers/discord_handler.py` - Format and send Discord embeds
- `models/match_schedule.py` - Match, MatchPlayers models
- `models/async_tournament.py` - Tournament model

## Future Enhancements

- [ ] Add match scheduled time to notification
- [ ] Include direct link to match page
- [ ] Add tournament logo/thumbnail to embed
- [ ] Show crew instructions/notes if configured
- [ ] Add quick action buttons (Accept/Decline for pending signups)
