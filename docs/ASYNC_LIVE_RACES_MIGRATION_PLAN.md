# Async Live Races Migration Plan

## Overview
This document outlines the plan for migrating the "Live Races" feature from the original SahasrahBot to SahaBot2. Live Races are scheduled, open-participation race events that differ from the standard async tournament format where individual players race asynchronously.

## Feature Description

### Original SahasrahBot Implementation
**Live Races** were a hybrid feature that combined elements of async tournaments with scheduled, synchronous race rooms:

- **Open Participation**: Unlike standard async races (player races individually in their own thread), live races are open to all eligible tournament participants
- **Scheduled Events**: Associated with a specific episode_id (scheduled time), similar to traditional tournament matches
- **RaceTime.gg Integration**: Creates actual race rooms on RaceTime.gg where multiple players compete simultaneously
- **Eligibility Checking**: Automatically determines which participants are eligible based on:
  - Pool availability (haven't exceeded runs_per_pool for that pool)
  - No active pending/in_progress races in the tournament
  - Account age requirements
- **Automatic Tracking**: When the race starts, creates AsyncTournamentRace records for each participant
- **Shared Permalink**: All participants race the same seed (permalink) at the same time

### Key Differences from Standard Async Races

| Feature | Standard Async Race | Live Race |
|---------|-------------------|-----------|
| **Participation** | Individual player, self-initiated | Open to all eligible players, scheduled |
| **Timing** | Asynchronous (player's choice) | Synchronous (scheduled time) |
| **Race Format** | Discord thread, manual timing | RaceTime.gg room, automatic timing |
| **Seed** | Random from pool | Specific seed for all participants |
| **Recording** | Manual submission by player | Automatic from RaceTime.gg results |
| **Creation** | Player-initiated via button | Admin-scheduled via web UI/API |

## Database Schema

### New Model: AsyncTournamentLiveRace

```python
class AsyncTournamentLiveRace(Model):
    """
    Live race event for async tournaments.
    
    Represents a scheduled race where all eligible participants race the same
    seed simultaneously on RaceTime.gg. Results are automatically recorded.
    """
    id = fields.IntField(pk=True)
    tournament = fields.ForeignKeyField('models.AsyncTournament', related_name='live_races')
    pool = fields.ForeignKeyField('models.AsyncTournamentPool', related_name='live_races')
    permalink = fields.ForeignKeyField('models.AsyncTournamentPermalink', related_name='live_races', null=True)
    
    # Scheduling
    episode_id = fields.IntField(null=True, unique=True)  # SpeedGaming episode ID (if applicable)
    scheduled_at = fields.DatetimeField(null=True)  # When race is scheduled to start
    match_title = fields.CharField(max_length=200, null=True)  # Display name for race
    
    # RaceTime.gg integration
    racetime_slug = fields.CharField(max_length=200, null=True, unique=True)  # e.g., "alttpr/cool-icerod-1234"
    racetime_goal = fields.CharField(max_length=255, null=True)  # RaceTime.gg goal
    room_open_time = fields.DatetimeField(null=True)  # When room was opened
    
    # Room configuration (optional override of tournament's profile)
    # If null, inherits from tournament.race_room_profile or org default profile
    race_room_profile = fields.ForeignKeyField(
        'models.RaceRoomProfile', 
        related_name='live_races',
        null=True
    )
    
    # Status tracking
    status = fields.CharField(max_length=45, default='scheduled')  
    # scheduled: Room not yet created
    # pending: Room created, waiting for race to start
    # in_progress: Race started
    # finished: Race completed
    # cancelled: Race cancelled
    
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    # related fields (reverse relations)
    races: fields.ReverseRelation["AsyncTournamentRace"]

    class Meta:
        table = "async_tournament_live_races"

    @property
    def racetime_url(self) -> Optional[str]:
        """Get RaceTime.gg URL for this race."""
        if not self.racetime_slug:
            return None
        return f"https://racetime.gg/{self.racetime_slug}"
    
    async def get_effective_profile(self) -> Optional['RaceRoomProfile']:
        """
        Get the effective race room profile for this live race.
        
        Priority:
        1. Live race's specific profile (if set)
        2. Tournament's profile (if set)
        3. Organization's default profile
        4. None (use system defaults)
        """
        if self.race_room_profile_id:
            await self.fetch_related('race_room_profile')
            return self.race_room_profile
        
        await self.fetch_related('tournament__race_room_profile')
        if self.tournament.race_room_profile_id:
            return self.tournament.race_room_profile
        
        # Get org default profile
        from application.services.race_room_profile_service import RaceRoomProfileService
        service = RaceRoomProfileService()
        return await service.get_default_profile_for_org(self.tournament.organization_id)
```

### Updates to AsyncTournamentRace

```python
class AsyncTournamentRace(Model):
    # ... existing fields ...
    
    # NEW: Link to live race (if this race was part of a live event)
    live_race = fields.ForeignKeyField(
        'models.AsyncTournamentLiveRace', 
        related_name='participant_races',
        null=True
    )
    
    # ... rest of model ...
```

## Architecture

### Module Structure

Keep the live races feature as a **separate module** from the standard async tournament feature:

```
application/
  services/
    async_tournament_service.py          # Standard async races
    async_live_race_service.py           # NEW: Live race management
    
  repositories/
    async_tournament_repository.py       # Standard async races
    async_live_race_repository.py        # NEW: Live race data access
    
models/
  async_tournament.py                    # Contains both models
  
views/
  tournaments/
    async_dashboard.py                   # Player dashboard (updated to show live races)
    async_review_queue.py                # Review queue (updated to filter live races)
    async_live_schedule.py               # NEW: Live race schedule view
    
components/
  dialogs/
    tournaments/
      create_live_race_dialog.py         # NEW: Admin dialog to create live race
      
api/
  routes/
    async_live_races.py                  # NEW: API endpoints for live races
```

### Separation of Concerns

**Why Keep It Separate:**
1. **Different Workflows**: Live races have completely different creation, scheduling, and recording workflows
2. **Different Permissions**: Live races require admin/mod creation; standard races are player-initiated
3. **Different UI/UX**: Live races need scheduling interfaces, room management, result recording
4. **Maintenance**: Easier to maintain and test as separate modules
5. **Future Extensions**: May want to add features specific to live races (e.g., spectator mode, commentary, brackets)

**Shared Components:**
- Models live in same file (`async_tournament.py`)
- Both use AsyncTournament as parent
- Both create AsyncTournamentRace records
- Both participate in scoring/leaderboards
- Both use same review queue (with filters)
- **Both leverage RaceRoomProfile for race room configuration**
  - Live races can use tournament's race_room_profile (if set)
  - Can override with live-race-specific profile
  - Falls back to organization's default profile
  - Eliminates need for hard-coded room settings

## Implementation Phases

### Phase 1: Data Layer (Week 1)

**Models & Migrations:**
- [ ] Create `AsyncTournamentLiveRace` model in `models/async_tournament.py`
- [ ] Add `live_race` foreign key to `AsyncTournamentRace`
- [ ] Create Aerich migration
- [ ] Apply migration to database

**Repository:**
- [ ] Create `AsyncLiveRaceRepository` in `application/repositories/`
  - `create_live_race(...)` - Create scheduled live race
  - `get_by_id(...)` - Get live race by ID
  - `get_by_episode_id(...)` - Get by SpeedGaming episode ID
  - `get_by_racetime_slug(...)` - Get by RaceTime.gg slug
  - `update_live_race(...)` - Update live race fields
  - `list_scheduled_races(...)` - Get upcoming scheduled races
  - `list_races_for_tournament(...)` - Get all live races for tournament
  - `get_eligible_participants(...)` - Get players eligible for live race
  - `create_participant_races(...)` - Create race records for participants

**Tests:**
- [ ] Repository tests for all CRUD operations
- [ ] Test eligibility logic
- [ ] Test organization scoping

### Phase 2: Business Logic (Week 2)

**Service Layer:**
- [ ] Create `AsyncLiveRaceService` in `application/services/`
  - **Admin Operations:**
    - `create_live_race(user, org_id, tournament_id, pool_id, scheduled_at, ...)` - Create live race
    - `update_live_race(user, org_id, live_race_id, ...)` - Update live race
    - `cancel_live_race(user, org_id, live_race_id)` - Cancel live race
    - `delete_live_race(user, org_id, live_race_id)` - Delete live race
  
  - **Race Management:**
    - `open_race_room(live_race_id)` - Create RaceTime.gg room (called by scheduler)
    - `process_race_start(live_race_id, race_room_data)` - Handle race start event
    - `process_race_finish(live_race_id, race_room_data)` - Handle race finish event
    - `record_live_race_results(user, org_id, racetime_slug)` - Manually record results
  
  - **Participant Management:**
    - `get_eligible_participants(live_race_id)` - Get list of eligible players
    - `check_player_eligibility(user_id, tournament_id, pool_id)` - Check specific player
  
  - **Queries:**
    - `get_live_race(user, org_id, live_race_id)` - Get live race details
    - `list_scheduled_races(user, org_id, tournament_id)` - Get upcoming races
    - `list_live_races(user, org_id, tournament_id, status=None)` - List all live races

**Authorization:**
- Create live race: `ASYNC_TOURNAMENT_ADMIN` or `ADMIN`
- Update/cancel/delete: `ASYNC_TOURNAMENT_ADMIN` or `ADMIN`
- Record results: `ASYNC_TOURNAMENT_ADMIN`, `ASYNC_REVIEWER`, or `ADMIN`
- View schedule: Tournament participants (organization members)
- View results: Same visibility as standard async races

**Events:**
- [ ] `AsyncLiveRaceCreatedEvent` - Live race scheduled
- [ ] `AsyncLiveRaceRoomOpenedEvent` - RaceTime.gg room created
- [ ] `AsyncLiveRaceStartedEvent` - Race countdown completed
- [ ] `AsyncLiveRaceFinishedEvent` - Race results recorded
- [ ] `AsyncLiveRaceCancelledEvent` - Race cancelled

**Tests:**
- [ ] Service tests for all operations
- [ ] Authorization tests
- [ ] Event emission tests

### Phase 3: RaceTime.gg Integration (Week 2-3)

**Race Room Management:**
- [ ] Extend `racetime/client.py` or create `racetime/async_live_handler.py`
  - **Use RaceRoomProfile for room configuration** (instead of hard-coded settings)
    - Live races can use tournament's assigned `race_room_profile`
    - Allows admins to configure room settings (start delay, time limit, streaming, chat permissions, etc.)
    - Falls back to organization's default profile if no tournament profile assigned
    - See `models/race_room_profile.py` for all available settings
  
  - Create race room with profile-derived settings:
    - `invitational=False` (open room - always for live races)
    - `unlisted=False` (public room - always for live races)
    - `streaming_required` - from profile
    - `auto_start` - from profile
    - `allow_comments` - from profile
    - `hide_comments` - from profile
    - `allow_prerace_chat` - from profile
    - `allow_midrace_chat` - from profile
    - `allow_non_entrant_chat` - from profile
    - `time_limit` - from profile (in hours)
    - `start_delay` - from profile (in seconds)
  
  - Set race info with tournament details
  - Invite eligible participants (or let them join)
  - Handle race lifecycle events:
    - Room created → Update live_race.racetime_slug, status='pending'
    - Race started → Create participant race records, status='in_progress'
    - Entrant finished → Update participant race end_time
    - Race finished → Record all results, status='finished'

**Eligibility Check on Join:**
- When player joins RaceTime.gg room, bot should:
  1. Look up player by racetime_id
  2. Check if they're eligible for the pool
  3. If not eligible, notify them (via bot message or DM)
  4. If eligible, create pending AsyncTournamentRace record

**Result Recording:**
- Automatic: Bot monitors race completion, records results
- Manual: Admin command to manually record from RaceTime.gg data
- Validation: Check for participants who finished but aren't eligible

**Tests:**
- [ ] Mock RaceTime.gg API responses
- [ ] Test room creation
- [ ] Test participant tracking
- [ ] Test result recording

### Phase 4: Task Scheduler Integration (Week 3)

**Scheduled Tasks:**
- [ ] Create task handler: `handle_async_live_race_room_open(task)`
  - Triggered 30-60 minutes before scheduled_at
  - Creates RaceTime.gg room
  - Updates live_race status
  - Sends notifications

- [ ] Update `TaskSchedulerService` to create tasks when live race is created

**Task Creation:**
```python
# When live race is created/updated with scheduled_at
if live_race.scheduled_at:
    room_open_time = live_race.scheduled_at - timedelta(minutes=30)
    await task_scheduler.schedule_task(
        task_type=TaskType.ASYNC_LIVE_RACE_OPEN,
        run_at=room_open_time,
        configuration={
            'live_race_id': live_race.id,
            'organization_id': live_race.tournament.organization_id,
        }
    )
```

**Tests:**
- [ ] Test task creation on live race schedule
- [ ] Test task execution
- [ ] Test task cleanup on cancellation

### Phase 5: API Endpoints (Week 4)

**Endpoints:**
```python
# GET /api/async-tournaments/{tournament_id}/live-races
# List all live races for tournament (with status filter)

# GET /api/async-tournaments/live-races/{live_race_id}
# Get specific live race details

# POST /api/async-tournaments/{tournament_id}/live-races
# Create new live race (admin only)

# PATCH /api/async-tournaments/live-races/{live_race_id}
# Update live race (admin only)

# DELETE /api/async-tournaments/live-races/{live_race_id}
# Delete live race (admin only)

# GET /api/async-tournaments/live-races/{live_race_id}/eligible
# Get list of eligible participants

# POST /api/async-tournaments/live-races/{live_race_id}/record
# Manually record race results (admin/reviewer only)
```

**Response Schemas:**
```python
@dataclass
class LiveRaceResponse:
    id: int
    tournament_id: int
    pool_id: int
    pool_name: str
    permalink_id: Optional[int]
    permalink_url: Optional[str]
    scheduled_at: Optional[datetime]
    match_title: Optional[str]
    racetime_slug: Optional[str]
    racetime_url: Optional[str]
    status: str
    participant_count: int
    created_at: datetime

@dataclass
class EligibleParticipantResponse:
    user_id: int
    discord_username: str
    eligible: bool
    reason: Optional[str]  # If not eligible
```

**Tests:**
- [ ] Endpoint integration tests
- [ ] Authorization tests
- [ ] Response schema validation

### Phase 6: UI Components (Week 5)

**Admin Views:**
- [ ] Live Race Creation Dialog (`components/dialogs/tournaments/create_live_race_dialog.py`)
  - Tournament selector
  - Pool selector
  - Date/time picker for scheduled_at
  - Title input
  - Permalink selector (optional, auto-selected if not provided)
  - **Race Room Profile selector** (optional - defaults to tournament's profile)
    - Show preview of profile settings
    - Option to use tournament default or select specific profile
    - Link to manage profiles
  - Preview eligible participants

- [ ] Live Race Management View (`views/tournaments/async_live_management.py`)
  - Table of scheduled live races
  - Actions: Edit, Cancel, Record Results
  - Filter by status (scheduled, pending, in_progress, finished, cancelled)
  - Participant count and eligibility info

**Player Views:**
- [ ] Live Race Schedule View (`views/tournaments/async_live_schedule.py`)
  - Calendar/list view of upcoming live races
  - Eligibility status for each race
  - Link to RaceTime.gg room (when open)
  - Countdown to race start

- [ ] Update Dashboard (`views/tournaments/async_dashboard.py`)
  - Add "Live Races" tab/section
  - Show player's participation in live races
  - Distinguish live race results from standard races
  - Filter/sort options

**Review Queue Updates:**
- [ ] Update `views/tournaments/async_review_queue.py`
  - Add filter for live vs. standard races
  - Show live race indicator in race list
  - Link to live race details

**Responsive Design:**
- All views must work on mobile and desktop
- Use `ResponsiveTable` for lists
- Mobile: Card layout for races
- Desktop: Table layout with sortable columns

**Tests:**
- [ ] UI component tests
- [ ] Dialog interaction tests
- [ ] Responsive layout tests

### Phase 7: Notifications & Discord Integration (Week 6)

**Discord Notifications:**
- [ ] Live Race Scheduled - Notify tournament channel
  - Include schedule, pool, eligibility info
  - Button to check personal eligibility

- [ ] Room Opened - Notify tournament channel
  - Include RaceTime.gg link
  - Tag eligible participants (optional)
  - Countdown to race start

- [ ] Race Started - Update tournament channel
  - List of participants
  - Link to room

- [ ] Race Finished - Post results to tournament channel
  - Top finishers
  - Link to full results
  - Note on review status

**Notification Handlers:**
- Create handlers in `application/services/notification_handlers/`
  - `async_live_race_scheduled_handler.py`
  - `async_live_race_room_opened_handler.py`
  - `async_live_race_started_handler.py`
  - `async_live_race_finished_handler.py`

**Event Subscriptions:**
```python
@EventBus.subscribe(AsyncLiveRaceCreatedEvent)
async def handle_live_race_scheduled(event: AsyncLiveRaceCreatedEvent):
    # Send Discord notification to tournament channel
    pass

@EventBus.subscribe(AsyncLiveRaceRoomOpenedEvent)
async def handle_live_race_room_opened(event: AsyncLiveRaceRoomOpenedEvent):
    # Send room link to tournament channel
    pass
```

**Tests:**
- [ ] Notification handler tests
- [ ] Event subscription tests
- [ ] Discord message format tests

### Phase 8: Documentation (Week 6)

**User Documentation:**
- [ ] Live Races User Guide (`docs/ASYNC_LIVE_RACES_USER_GUIDE.md`)
  - What are live races
  - How to participate
  - Eligibility requirements
  - Schedule viewing
  - Results and scoring

**Admin Documentation:**
- [ ] Live Races Admin Guide (`docs/ASYNC_LIVE_RACES_ADMIN_GUIDE.md`)
  - Creating live races
  - Scheduling considerations
  - Managing rooms
  - Recording results
  - Troubleshooting

**Developer Documentation:**
- [ ] Live Races Architecture (`docs/ASYNC_LIVE_RACES_ARCHITECTURE.md`)
  - System design
  - Database schema
  - API reference
  - Event system
  - Integration points

- [ ] Update existing docs:
  - [ ] `docs/ASYNC_TOURNAMENT_END_USER_GUIDE.md` - Add live races section
  - [ ] `docs/ASYNC_RACE_REVIEW.md` - Add live race filtering
  - [ ] `docs/EVENT_SYSTEM.md` - Document live race events

### Phase 9: Testing & Refinement (Week 7)

**Integration Testing:**
- [ ] End-to-end test: Create → Schedule → Open → Start → Finish → Record
- [ ] Test with multiple participants
- [ ] Test eligibility checking
- [ ] Test result recording
- [ ] Test notifications

**Edge Cases:**
- [ ] Player joins room but isn't eligible
- [ ] Race room cancelled on RaceTime.gg
- [ ] Network failure during result recording
- [ ] Multiple live races for same tournament
- [ ] Live race conflicts with standard async races

**Performance:**
- [ ] Test with large participant counts (100+ players)
- [ ] Query optimization for eligibility checks
- [ ] Caching for frequently accessed data

**User Acceptance Testing:**
- [ ] Admin workflow testing
- [ ] Player workflow testing
- [ ] Mobile app testing
- [ ] Discord bot testing

## Migration from Original SahasrahBot

### Data Migration (If Applicable)

If migrating existing live race data:

```sql
-- Map old AsyncTournamentLiveRace to new structure
INSERT INTO async_tournament_live_races (
    tournament_id,
    pool_id,
    permalink_id,
    episode_id,
    scheduled_at,
    match_title,
    racetime_slug,
    status,
    created_at,
    updated_at
)
SELECT
    alt.tournament_id,
    alt.pool_id,
    alt.permalink_id,
    alt.episode_id,
    NULL, -- scheduled_at (not in old schema)
    alt.match_title,
    alt.racetime_slug,
    CASE alt.status
        WHEN 'scheduled' THEN 'scheduled'
        WHEN 'pending' THEN 'pending'
        WHEN 'in_progress' THEN 'in_progress'
        WHEN 'finished' THEN 'finished'
        ELSE 'cancelled'
    END,
    alt.created,
    alt.updated
FROM old_async_tournament_live_races alt
WHERE alt.tournament_id IN (
    -- Only tournaments being migrated
    SELECT id FROM async_tournaments WHERE organization_id = ?
);

-- Update AsyncTournamentRace records to link to live races
UPDATE async_tournament_races atr
SET live_race_id = (
    SELECT id FROM async_tournament_live_races
    WHERE racetime_slug = (
        SELECT racetime_slug FROM old_async_tournament_live_races
        WHERE id = atr.old_live_race_id
    )
)
WHERE atr.old_live_race_id IS NOT NULL;
```

### Configuration Changes

**Environment Variables:**
```env
# Add to .env
ASYNC_LIVE_RACE_ROOM_OPEN_MINUTES=30  # How long before scheduled_at to open room
ASYNC_LIVE_RACE_MIN_ACCOUNT_AGE_DAYS=7  # Minimum Discord account age for live races
```

**Organization Settings:**
```python
# Add to Organization model (if needed)
class Organization(Model):
    # ...
    allow_async_live_races = fields.BooleanField(default=False)
    live_race_account_age_days = fields.IntField(default=7)
```

## Security Considerations

### Authorization
- **Live Race Creation**: Only admins can create/update/delete live races
- **Result Recording**: Admins and reviewers can manually record results
- **Eligibility Viewing**: Any tournament participant can view eligibility
- **Organization Scoping**: All operations must validate organization membership

### Data Validation
- Scheduled time must be in future
- Pool must belong to tournament
- Tournament must be active
- Permalink must exist in pool (if specified)
- RaceTime.gg slug must be unique

### Rate Limiting
- Limit live race creation to prevent abuse
- Throttle result recording API calls
- Discord notification rate limits

## Monitoring & Metrics

### Key Metrics
- Live races created per tournament
- Average participation rate
- Room creation success rate
- Result recording success rate
- Average time from finish to recording

### Logging
- Log all live race lifecycle events
- Log eligibility check results
- Log RaceTime.gg API interactions
- Log result recording attempts

### Alerts
- Failed room creation
- Failed result recording
- Unclaimed scheduled races (no room created)
- Finished races not recorded within 1 hour

## Future Enhancements

### Phase 11+ (Post-Launch)
- **Bracket Integration**: Seed live races from tournament brackets
- **Spectator Mode**: Special view for watching live races
- **Commentary Tools**: Integration for race commentary
- **Replay Links**: Store VODs from all participants
- **Live Leaderboard**: Real-time standings during race
- **Qualification System**: Use live races as qualifiers for bracket stages
- **Multi-Heat Races**: Support for multiple heats/rounds
- **Team Races**: Support for team-based live races
- **Seeding**: Seed participant start order based on performance

## Dependencies

### Required
- RaceTime.gg API access
- Discord bot permissions (message sending, channel management)
- Task scheduler system
- Event bus system
- **RaceRoomProfile system** (already implemented)
  - Live races leverage existing `RaceRoomProfile` model and services
  - Provides configurable room settings (start delay, time limit, chat permissions, etc.)
  - Allows per-tournament or per-live-race configuration
  - See `models/race_room_profile.py` and `application/services/race_room_profile_service.py`

### Optional
- SpeedGaming API (for episode_id integration)
- Streaming platform APIs (Twitch, YouTube) for VOD collection
- Analytics platform for metrics

## Timeline Summary

| Phase | Duration | Description |
|-------|----------|-------------|
| 1 | Week 1 | Data Layer (models, repository) |
| 2 | Week 2 | Business Logic (service, events) |
| 3 | Week 2-3 | RaceTime.gg Integration |
| 4 | Week 3 | Task Scheduler Integration |
| 5 | Week 4 | API Endpoints |
| 6 | Week 5 | UI Components |
| 7 | Week 6 | Notifications & Discord |
| 8 | Week 6 | Documentation |
| 9 | Week 7 | Testing & Refinement |

**Total Estimated Time**: 7 weeks for full implementation

## Success Criteria

- [ ] Admins can create and schedule live races
- [ ] System automatically opens RaceTime.gg rooms at scheduled times
- [ ] Players can view schedule and check eligibility
- [ ] Eligible participants can join races
- [ ] Results are automatically recorded from RaceTime.gg
- [ ] Races appear in review queue with live race indicator
- [ ] Scores are calculated and included in leaderboards
- [ ] Discord notifications are sent at key milestones
- [ ] All features work on mobile and desktop
- [ ] All operations are organization-scoped
- [ ] Comprehensive documentation is available

## Questions for Clarification

1. **Scheduling Source**: Will live races only use manual scheduling, or should we integrate with SpeedGaming API for automated scheduling?

2. **Participant Invitations**: Should the bot auto-invite eligible participants to the RaceTime.gg room, or let them join organically?

3. **Account Age Validation**: Should the 7-day account age requirement be configurable per tournament/organization?

4. **Result Recording**: Should we support both automatic (on race finish) and manual (admin command) recording?

5. **Notifications**: Should we notify individual players when a live race they're eligible for is scheduled?

6. **Streaming Requirements**: Should live races enforce streaming_required on RaceTime.gg?

7. **Reattempts**: Can players reattempt live races if they forfeit, or is it one-shot only?

8. **Multiple Pools**: Can a single live race event span multiple pools, or is it always one pool per race?

---

**Document Version**: 1.0  
**Last Updated**: 2025-01-04  
**Status**: Planning Phase
