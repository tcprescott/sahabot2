# Match Handler Integration Testing Guide

This document provides manual testing steps to verify the RaceTime match handler integration functionality.

## Background

The system now automatically includes the Match handler mixin (`MatchRaceMixin`) when:
1. Opening a RaceTime room for a match
2. Rejoining a room linked to a match (after bot disconnect, restart, or application restart)

Additionally, administrators can configure which handler class each RaceTime bot uses globally.

## Prerequisites

- Access to admin panel (ADMIN or SUPERADMIN permission)
- At least one RaceTime bot configured
- A tournament with matches configured
- RaceTime.gg integration set up

## Test Cases

### 1. Handler Selection in Admin UI

**Test**: Verify administrators can select handler class when creating/editing bots.

**Steps**:
1. Navigate to Admin → RaceTime Bots
2. Click "Add Bot" button
3. Fill in required fields (category, name, client ID, client secret)
4. Locate "Handler Class" dropdown
5. Verify available options:
   - SahaRaceHandler (default)
   - ALTTPRRaceHandler
   - SMRaceHandler
   - SMZ3RaceHandler
   - AsyncLiveRaceHandler
6. Hover over info icon to see tooltip
7. Select a handler (e.g., ALTTPRRaceHandler)
8. Create the bot
9. Edit the bot and verify handler class is displayed correctly
10. Change handler class and save
11. Restart the bot
12. Verify bot uses new handler class (check logs for handler name)

**Expected Result**:
- Dropdown shows all available handlers
- Tooltip explains handler class purpose
- Selected handler is saved and displayed correctly
- Bot uses selected handler after restart

**Verification**:
```bash
# Check bot logs for handler initialization
grep "handler=" logs/sahabot2.log
# Should show: handler=ALTTPRRaceHandler (or selected handler)
```

---

### 2. Match Room Creation with Match Handler

**Test**: Verify match-specific handler is used when creating a room for a match.

**Steps**:
1. Navigate to Tournament → Matches
2. Select a match with players assigned
3. Click "Open RaceTime Room" button
4. Wait for room to be created
5. Check application logs for handler creation messages
6. Verify room is created successfully

**Expected Result**:
- Room is created successfully
- Logs show match handler being used
- Handler has both category commands AND match processing

**Log Verification**:
```bash
# Check for match handler creation
grep "Created match handler for race" logs/sahabot2.log
grep "MatchRaceMixin" logs/sahabot2.log
```

**Example Log Entry**:
```
Created match handler for race alttpr/cool-doge-1234 (match_id=42)
```

---

### 3. Bot Restart with Open Match Rooms

**Test**: Verify bot rejoins match rooms with match handler after restart.

**Steps**:
1. Create a RaceTime room for a match (see Test 2)
2. Verify room is open and active
3. Restart the application server
4. Wait for bot to reconnect
5. Check logs for room rejoining messages
6. Verify match handler is used for rejoined rooms

**Expected Result**:
- Bot reconnects successfully
- Bot rejoins all open match rooms
- Match handlers are used (not base handlers)
- Match processing continues working

**Log Verification**:
```bash
# Check for room rejoining
grep "Rejoining open RaceTime rooms" logs/sahabot2.log
grep "Successfully rejoined room .* with match handler" logs/sahabot2.log
grep "Room .* is for match .*, using match handler" logs/sahabot2.log
```

---

### 4. Bot Disconnect/Reconnect

**Test**: Verify bot rejoins match rooms correctly after temporary disconnect.

**Steps**:
1. Create a RaceTime room for a match
2. Simulate network issue or bot disconnection (stop bot via admin UI)
3. Verify room remains open on RaceTime.gg
4. Restart bot via admin UI
5. Check logs for reconnection and room rejoining
6. Verify match handler is used

**Expected Result**:
- Bot reconnects successfully
- Bot rejoins match room with match handler
- Match continues processing correctly

---

### 5. Race Status Changes Update Match Status

**Test**: Verify match status advances when race status changes.

**Steps**:
1. Create a RaceTime room for a match
2. Start the race (begin countdown)
3. Verify match status changes to "started" when race goes in_progress
4. Complete the race
5. Verify match status changes to "finished" when race completes
6. Check match player finish ranks are recorded

**Expected Result**:
- Match `checked_in_at` set when room opens
- Match `started_at` set when race starts
- Match `finished_at` set when race finishes
- Player finish ranks recorded correctly

**Database Verification**:
```sql
-- Check match status timestamps
SELECT id, checked_in_at, started_at, finished_at 
FROM matches 
WHERE id = <match_id>;

-- Check player finish ranks
SELECT user_id, finish_rank 
FROM match_players 
WHERE match_id = <match_id>;
```

---

### 6. Race Cancellation Unlinks Room

**Test**: Verify room is unlinked from match when race is cancelled.

**Steps**:
1. Create a RaceTime room for a match
2. Cancel the race on RaceTime.gg (use race monitor or bot command)
3. Wait for event to propagate
4. Check logs for room unlinking message
5. Verify room is no longer linked to match in database

**Expected Result**:
- Race cancellation detected by bot
- Room unlinked from match automatically
- Match remains in database (not deleted)
- Room record is deleted from `racetime_rooms` table

**Log Verification**:
```bash
# Check for cancellation handling
grep "race cancelled" logs/sahabot2.log
grep "Auto-unlinked RaceTime room .* from match" logs/sahabot2.log
```

**Database Verification**:
```sql
-- Room should be deleted
SELECT * FROM racetime_rooms WHERE slug = '<room_slug>';
-- Should return 0 rows

-- Match should still exist
SELECT * FROM matches WHERE id = <match_id>;
-- Should return the match
```

---

### 7. Non-Match Rooms Use Base Handler

**Test**: Verify regular (non-match) rooms still use base handler.

**Steps**:
1. Use RaceTime.gg website to create a room (not via match)
2. Have bot join room manually (if configured)
3. Check logs for handler type
4. Verify base handler is used (not match handler)

**Expected Result**:
- Bot uses base handler (e.g., ALTTPRRaceHandler)
- No match processing occurs
- Race commands work normally

**Log Verification**:
```bash
# Should NOT see "match handler" messages
grep "Created handler for race" logs/sahabot2.log
# Should NOT show match_id
```

---

## Common Issues and Troubleshooting

### Issue: Bot not rejoining rooms after restart

**Check**:
1. Bot credentials are valid
2. Bot has permission to access rooms
3. Database connection is working
4. RaceTime.gg is accessible

**Debug**:
```bash
# Check bot connection status
grep "Racetime bot.*started successfully" logs/sahabot2.log
grep "Rejoining open RaceTime rooms" logs/sahabot2.log
```

### Issue: Match handler not being used

**Check**:
1. Room is actually linked to a match in database
2. `RacetimeRoom` table has correct `match_id`
3. Bot restart completed successfully

**Debug**:
```sql
-- Verify room-match linkage
SELECT * FROM racetime_rooms WHERE slug = '<room_slug>';
```

### Issue: Handler class not changing after edit

**Check**:
1. Bot was restarted after changing handler class
2. Changes were saved successfully
3. No errors in logs during restart

**Fix**:
```
1. Go to Admin → RaceTime Bots
2. Stop the bot
3. Edit and save handler class
4. Start the bot
5. Verify in logs
```

---

## Test Completion Checklist

- [ ] Handler selection UI shows dropdown with all options
- [ ] Handler selection UI shows tooltip
- [ ] Created bot uses selected handler
- [ ] Edited bot uses updated handler
- [ ] Match room creation uses match handler
- [ ] Bot restart rejoins rooms with match handlers
- [ ] Bot reconnect uses match handlers
- [ ] Race start updates match status
- [ ] Race finish updates match status and records results
- [ ] Race cancellation unlinks room from match
- [ ] Non-match rooms use base handlers

---

## Reference

### Match Handler Classes

- **MatchSahaRaceHandler**: Base commands + match processing
- **MatchALTTPRRaceHandler**: ALTTPR commands + match processing
- **MatchSMRaceHandler**: SM commands + match processing
- **MatchSMZ3RaceHandler**: SMZ3 commands + match processing

These are dynamically created by combining `MatchRaceMixin` with the base handler class.

### Key Log Messages

```
Room <slug> is for match <id>, using match handler
Created match handler for race <slug> (match_id=<id>)
Successfully rejoined room <slug> with match handler
Auto-advanced match <id> to 'started' status (race in progress)
Auto-advanced match <id> to 'finished' status (race finished)
Auto-unlinked RaceTime room <slug> from match <id> (race cancelled)
```

### Database Tables

- `racetime_bots`: Bot configurations (includes `handler_class`)
- `racetime_rooms`: Room-match linkages
- `matches`: Match status timestamps
- `match_players`: Player finish ranks
