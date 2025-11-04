# Phase 3 & 6 Implementation Summary

## Overview
Implemented Phase 3 (RaceTime.gg Integration) and Phase 6 (UI Components) for the Async Tournament Live Races feature.

## Phase 3: RaceTime.gg Integration

### Files Created/Modified

#### 1. `racetime/live_race_handler.py` (NEW)
- **Purpose**: Custom race handler for live races extending SahaRaceHandler
- **Key Features**:
  - Tracks live_race_id for correlation with database records
  - Automatically processes race start events
  - Automatically processes race finish events
  - Extracts participant racetime IDs and results
  - Calls AsyncLiveRaceService for all business logic
- **Integration**: Listens to RaceTime.gg race_data updates and triggers service methods

#### 2. `application/services/async_live_race_service.py` (MODIFIED)
- **Updated**: `open_race_room()` method
- **Changes**:
  - Removed placeholder slug generation
  - Integrated with real RacetimeBot via `get_racetime_bot_instance()`
  - Gets effective RaceRoomProfile via `live_race.get_effective_profile()`
  - Converts profile settings to RaceTime API parameters
  - Creates race room on RaceTime.gg via `bot.startrace()`
  - Replaces generic handler with AsyncLiveRaceHandler
  - Updates database with actual racetime_slug from created room
  - Proper error handling and logging
  
- **Added**: `_profile_to_race_params()` helper method
- **Purpose**: Maps RaceRoomProfile fields to RaceTime.gg API parameters
- **Mapping**:
  - `streaming_required` → `streaming_required`
  - `auto_start` → `auto_start`
  - `allow_comments` → `allow_comments`
  - `hide_comments` → `hide_comments`
  - `allow_prerace_chat` → `allow_prerace_chat`
  - `allow_midrace_chat` → `allow_midrace_chat`
  - `allow_non_entrant_chat` → `allow_non_entrant_chat`
  - `time_limit` → `time_limit` (hours)
  - `start_delay` → `start_delay` (seconds)
  - Always sets `invitational=False` and `unlisted=False` (live races are public)

### Integration Flow

1. **Task Scheduler** calls `handle_async_live_race_open()` 30 minutes before scheduled time
2. **Handler** calls `AsyncLiveRaceService.open_race_room()`
3. **Service**:
   - Gets effective RaceRoomProfile
   - Gets RacetimeBot instance for category ('alttpr')
   - Converts profile to race parameters
   - Calls `bot.startrace()` to create room on RaceTime.gg
   - Replaces generic handler with AsyncLiveRaceHandler
   - Updates database with racetime_slug
   - Emits AsyncLiveRaceRoomOpenedEvent
4. **AsyncLiveRaceHandler**:
   - Monitors race status changes
   - When race starts: Calls `service.process_race_start()` with participant IDs
   - When race finishes: Calls `service.process_race_finish()` with results
5. **Service** creates AsyncTournamentRace records and emits events

### Key Benefits
- Fully automated race room creation
- Automatic participant tracking
- Automatic result recording
- No manual intervention required
- Uses RaceRoomProfile for consistent configuration

## Phase 6: UI Components

### Files Created

#### 1. `components/dialogs/tournaments/create_live_race_dialog.py` (NEW)
- **Purpose**: Admin dialog for scheduling new live races
- **Extends**: BaseDialog
- **Features**:
  - Pool selection (required dropdown)
  - Scheduled date picker (required, defaults to tomorrow)
  - Scheduled time picker (required, defaults to 20:00 UTC)
  - Match title input (optional text)
  - Permalink selection (optional dropdown with "Use pool default" option)
  - Episode ID input (optional number)
  - Race room profile selection (optional dropdown with "Use tournament default" option)
  - Validation:
    - Ensures pool is selected
    - Ensures date/time are provided
    - Ensures scheduled time is in future
    - Validates episode_id is numeric
  - Error display with red message banner
  - Calls AsyncLiveRaceService.create_live_race() on submit
  - Callback support for refreshing parent view

**Export**: Added to `components/dialogs/tournaments/__init__.py`

#### 2. `views/tournaments/async_live_races.py` (NEW)
- **Purpose**: Management view for tournament live races
- **Class**: AsyncLiveRacesView
- **Features**:
  - **Header**:
    - "Schedule Live Race" button (admin only)
    - Status filter dropdown (all/scheduled/pending/in_progress/finished/cancelled)
  - **Responsive Table**:
    - Status column with colored badges
    - Scheduled datetime column (localized)
    - Pool name column
    - Match title column
    - RaceTime.gg link column (or "Not opened yet")
    - Actions column (admin only):
      - View eligible participants button
      - Cancel race button (if not finished/cancelled)
      - Delete race button (if scheduled/cancelled only)
  - **Dialogs**:
    - Create live race dialog (opens CreateLiveRaceDialog)
    - View eligible participants dialog (shows list with icons)
    - Confirm cancel dialog (with ConfirmDialog)
    - Confirm delete dialog (with ConfirmDialog)
  - **Permissions**:
    - Public viewing of races
    - Admin-only management actions
    - Uses AsyncTournamentService.can_manage_async_tournaments()
  - **Real-time updates**:
    - Refresh after create/cancel/delete operations
    - Filter updates refresh table dynamically

**Export**: Added to `views/tournaments/__init__.py`

### UI Integration Points

To integrate the new Live Races view into the tournament management interface:

1. **Add to Tournament Management Page**:
   ```python
   # In tournament_management view or async_dashboard
   from views.tournaments import AsyncLiveRacesView
   
   # Add "Live Races" tab/section
   with ui.tab('Live Races'):
       view = AsyncLiveRacesView(user, tournament)
       await view.render()
   ```

2. **Add to Tournament Navigation**:
   ```python
   # Add link in tournament sidebar/menu
   ui.link('Live Races', f'/org/{org_id}/async/{tournament_id}/live-races')
   ```

3. **Optional Dashboard Widget**:
   ```python
   # Show next upcoming live race in dashboard
   upcoming = await service.list_scheduled_races(org_id, tournament_id)
   if upcoming:
       next_race = upcoming[0]
       with Card.create(title='Next Live Race'):
           ui.label(f'Pool: {next_race.pool.name}')
           DateTimeLabel.create(next_race.scheduled_at)
           if next_race.racetime_url:
               ui.link('Join on RaceTime.gg', next_race.racetime_url)
   ```

### User Workflows

#### Tournament Administrator:
1. Navigate to tournament's Live Races tab
2. Click "Schedule Live Race" button
3. Fill in dialog:
   - Select pool
   - Pick date and time (UTC)
   - Optionally set title, permalink, episode ID, profile
4. Click "Create"
5. Race appears in table with "scheduled" status
6. 30 minutes before scheduled time:
   - System creates room on RaceTime.gg
   - Status changes to "pending"
   - RaceTime.gg link appears
7. When race starts on RaceTime.gg:
   - Status changes to "in_progress"
   - Race records created for participants
8. When race finishes:
   - Status changes to "finished"
   - Results automatically recorded

#### Tournament Participant:
1. Navigate to tournament's Live Races tab
2. View upcoming races filtered by status
3. See scheduled time (in local timezone)
4. When room opens, click "View Race" link
5. Join race on RaceTime.gg
6. Race and finish normally
7. Results automatically recorded in tournament

### Mobile Responsiveness
Both components follow mobile-first patterns:
- **Dialog**: Uses responsive form grid (2 columns desktop, 1 column mobile)
- **Table**: ResponsiveTable automatically stacks on mobile
- **Actions**: Button groups wrap on small screens
- **Filters**: Dropdowns adjust width for mobile
- **Cards**: Full-width on mobile with proper spacing

## Testing Checklist

### Phase 3 Testing
- [ ] Verify RaceTime bot is running for 'alttpr' category
- [ ] Create live race via API/UI
- [ ] Wait for scheduled time (or manually trigger task)
- [ ] Verify room created on RaceTime.gg
- [ ] Verify racetime_slug updated in database
- [ ] Verify status changes from 'scheduled' → 'pending'
- [ ] Start race on RaceTime.gg
- [ ] Verify status changes to 'in_progress'
- [ ] Verify race records created for participants
- [ ] Finish race on RaceTime.gg
- [ ] Verify status changes to 'finished'
- [ ] Verify results recorded in race records
- [ ] Verify events emitted at each stage

### Phase 6 Testing
- [ ] Access Live Races view as admin
- [ ] Verify "Schedule Live Race" button visible
- [ ] Click button, verify dialog opens
- [ ] Fill in all fields, verify validation
- [ ] Submit invalid data, verify errors shown
- [ ] Submit valid data, verify race created
- [ ] Verify race appears in table
- [ ] Test status filter (all/scheduled/pending/etc)
- [ ] Click "View Eligible Participants"
- [ ] Verify participant list shown
- [ ] Click "Cancel" on in_progress race
- [ ] Verify confirmation dialog, confirm cancellation
- [ ] Verify status updated to 'cancelled'
- [ ] Click "Delete" on cancelled race
- [ ] Verify confirmation dialog, confirm deletion
- [ ] Verify race removed from table
- [ ] Test on mobile viewport (table stacking, responsive layout)
- [ ] Access view as non-admin user
- [ ] Verify management buttons hidden
- [ ] Verify can still view races and filter

## Next Steps (Phase 7)

Phase 7 will implement notifications and Discord integration:

1. **Discord Announcements**:
   - When live race created → Announce in tournament Discord channel
   - When room opens → Post link with @here ping
   - When race starts → Update announcement
   - When race finishes → Post results

2. **Event Handlers**:
   - Subscribe to AsyncLiveRaceCreatedEvent
   - Subscribe to AsyncLiveRaceRoomOpenedEvent
   - Subscribe to AsyncLiveRaceStartedEvent
   - Subscribe to AsyncLiveRaceFinishedEvent

3. **Discord Commands** (optional):
   - `/liveraces upcoming` - Show upcoming live races
   - `/liveraces schedule <pool> <datetime>` - Schedule a race (admin)
   - `/liveraces cancel <id>` - Cancel a race (admin)

4. **Email Notifications** (optional):
   - Email participants when room opens
   - Reminder emails 1 hour before scheduled time

All core functionality is now complete! The feature is ready for integration into the application.
