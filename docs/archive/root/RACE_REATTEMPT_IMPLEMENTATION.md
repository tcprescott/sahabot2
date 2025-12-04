# Race Re-attempt System Implementation

## Overview

Implemented a comprehensive race re-attempt system for async qualifiers that allows players to re-attempt races with configurable limits. Re-attempted races are marked and excluded from scoring calculations.

**Implementation Date**: November 10, 2025

## Features Implemented

### 1. Database Schema

**File**: `models/async_qualifier.py`
- Added `max_reattempts` field (SmallIntField, default=-1)
  - -1 = unlimited re-attempts
  - 0 = no re-attempts allowed
  - >0 = specific limit per player
- Existing `reattempted` field on `AsyncTournamentRace` model already present

**Migration**: `migrations/models/55_20251110005745_add_max_reattempts_to_async_qualifier.py`
- Status: ✅ Applied
- SQL: `ALTER TABLE async_qualifiers ADD max_reattempts SMALLINT NOT NULL DEFAULT -1`

### 2. Repository Layer

**File**: `application/repositories/async_qualifier_repository.py`

New methods:
- `count_reattempted_races(user_id, tournament_id)` - Count reattempted races for a user
- `mark_race_reattempted(race_id)` - Mark a race as reattempted

### 3. Service Layer

**File**: `application/services/tournaments/async_qualifier_service.py`

New methods:

#### `get_reattempt_count(user, organization_id, tournament_id)`
- Returns count of reattempted races for a user in a tournament
- Used to check against max_reattempts limit

#### `can_reattempt_race(user, organization_id, race_id)`
- Validates whether a race can be re-attempted
- Checks:
  - Race exists and belongs to the user
  - Race status is "finished" or "forfeit"
  - Race not already reattempted
  - Re-attempts not disabled (max_reattempts != 0)
  - User hasn't exceeded max_reattempts limit (if > 0)
- Returns: `(bool, Optional[str])` tuple (allowed, reason if not allowed)

#### `mark_race_as_reattempted(user, organization_id, race_id)`
- Marks a race as reattempted
- Creates audit log entry
- Recalculates permalink scores (excluding reattempted races)
- Returns: `Optional[AsyncTournamentRace]`

**Existing Methods (Already Correct)**:
- `calculate_permalink_scores()` - Already filters `reattempted=False` at lines 843 and 877

### 4. UI Components

#### Race Re-attempt Dialog
**File**: `components/dialogs/tournaments/race_reattempt_dialog.py` (NEW)

Complete dialog component with:
- Validation via `can_reattempt_race()` before showing
- Warning section about exclusion from scoring
- Race information display (tournament, pool, status, time, score)
- Re-attempt limit information:
  - Shows "not allowed" message if max_reattempts = 0
  - Shows current count and max allowed if max_reattempts > 0
  - Shows "unlimited" message if max_reattempts = -1
- Cancel and Re-attempt action buttons
- Success callback after re-attempt

#### Player History View
**File**: `views/tournaments/async_player_history.py` (MODIFIED)

Added:
- Actions column with re-attempt button
- Re-attempt button only shown for:
  - Current user's own races
  - Races with status "finished" or "forfeit"
  - Races not already reattempted
- `_render_actions()` method - Renders action buttons
- `_show_reattempt_dialog()` method - Shows confirmation dialog
- `_on_reattempt_success()` method - Refreshes view after re-attempt

#### Tournament Admin Dialog
**File**: `components/dialogs/tournaments/async_qualifier_dialog.py` (MODIFIED)

Added:
- `max_reattempts_input` field
- Number input with:
  - Min: -1 (unlimited)
  - Max: 100
  - Default: -1
  - Help text: "Maximum number of re-attempts per player (-1 = unlimited, 0 = none)"
- Validation for values >= -1
- Included in create/update data

### 5. Exports

**File**: `components/dialogs/tournaments/__init__.py` (MODIFIED)
- Added `RaceReattemptDialog` to imports and `__all__` exports

## Architecture Compliance

✅ **Four-Layer Architecture**
- Model: `AsyncTournament.max_reattempts`, `AsyncTournamentRace.reattempted`
- Repository: Data access methods
- Service: Business logic and validation
- UI: Dialogs and views

✅ **Authorization**
- Re-attempts only allowed for user's own races
- Service layer validates user ownership

✅ **Audit Logging**
- All re-attempts logged via `AuditService`

✅ **Event System**
- Score recalculation triggered after re-attempt

✅ **Type Safety**
- Full type hints on all methods
- Proper Optional[T] usage

✅ **Documentation**
- Comprehensive docstrings
- Clear parameter descriptions
- Return type documentation

## User Flow

1. **Player views their race history**
   - Navigate to tournament → Player History
   - See all races with status and scores

2. **Player decides to re-attempt**
   - Click "Re-attempt" button on finished/forfeit race
   - Dialog shows warning about score exclusion
   - Dialog displays current re-attempt count and limit

3. **Player confirms re-attempt**
   - System validates eligibility
   - Race marked as reattempted
   - Permalink scores recalculated (excluding reattempted races)
   - View refreshes to show updated status

4. **Player starts new race**
   - Previous race no longer counts toward scoring
   - New race can be attempted on same permalink

## Administrator Configuration

**Setting Re-attempt Limits**:
1. Navigate to Organization Admin → Async Qualifiers
2. Create or edit tournament
3. Set "Max Re-attempts" field:
   - -1 = Unlimited re-attempts
   - 0 = No re-attempts allowed
   - N = Maximum N re-attempts per player

## Score Calculation Behavior

**Existing Logic (No Changes Required)**:
- `calculate_permalink_scores()` already filters `reattempted=False`
- Re-attempted races automatically excluded from:
  - Par time calculation (line 843)
  - Player score updates (line 877)
- No additional changes needed to scoring system

## Testing Checklist

### Backend Testing
- [ ] Create tournament with max_reattempts=-1 (unlimited)
- [ ] Create tournament with max_reattempts=0 (none allowed)
- [ ] Create tournament with max_reattempts=3 (limited)
- [ ] Complete a race (status: finished)
- [ ] Forfeit a race (status: forfeit)
- [ ] Re-attempt a finished race (unlimited tournament)
- [ ] Verify race marked as reattempted
- [ ] Verify score calculation excludes reattempted race
- [ ] Verify re-attempt count increments
- [ ] Attempt re-attempt when max_reattempts=0 (should fail)
- [ ] Attempt to exceed max_reattempts limit (should fail)
- [ ] Verify error messages when not allowed
- [ ] Verify audit log entry created

### UI Testing
- [ ] View player history as current user
- [ ] See re-attempt button on finished races
- [ ] See re-attempt button on forfeit races
- [ ] No re-attempt button on in-progress races
- [ ] No re-attempt button on already reattempted races
- [ ] Click re-attempt button → dialog shows
- [ ] Dialog displays race information
- [ ] Dialog displays limit information
- [ ] Dialog shows correct current count
- [ ] Confirm re-attempt → race updated
- [ ] View refreshes showing "Reattempted: Yes"
- [ ] Cannot re-attempt the same race twice
- [ ] Re-attempt button disappears after re-attempt

### Admin Testing
- [ ] Create tournament with max_reattempts field
- [ ] Edit tournament to change max_reattempts
- [ ] Verify validation (no negative values)
- [ ] Verify tournaments saved with correct limit

## Future Enhancements

Potential improvements:
1. **Discord Bot Integration**
   - Add `/reattempt` command for Discord bot
   - Show re-attempt limits in Discord UI

2. **Re-attempt History**
   - Track which races were re-attempted when
   - Show history of re-attempts for a permalink

3. **Partial Re-attempts**
   - Allow re-attempting specific permalinks only
   - Different limits per pool

4. **Admin Override**
   - Allow admins to manually mark races as reattempted
   - Allow admins to reset re-attempt counts

5. **Notifications**
   - Notify user when approaching re-attempt limit
   - Notify when re-attempt limit reached

## Files Changed

### New Files (2)
1. `components/dialogs/tournaments/race_reattempt_dialog.py` - Dialog component
2. `migrations/models/55_20251110005745_add_max_reattempts_to_async_qualifier.py` - Migration

### Modified Files (6)
1. `models/async_qualifier.py` - Added max_reattempts field
2. `application/repositories/async_qualifier_repository.py` - Added 2 methods
3. `application/services/tournaments/async_qualifier_service.py` - Added 3 methods, updated create_tournament
4. `components/dialogs/tournaments/__init__.py` - Exported new dialog
5. `components/dialogs/tournaments/async_qualifier_dialog.py` - Added max_reattempts input
6. `views/tournaments/async_player_history.py` - Added Actions column and dialog integration

### Total Changes
- **Lines Added**: ~300
- **Methods Added**: 8
- **UI Components Added**: 1 dialog + 1 column
- **Database Fields Added**: 1

## Known Limitations

1. **No bulk re-attempt**: Can only re-attempt one race at a time
2. **No re-attempt undo**: Once marked as reattempted, cannot be unmarked (admin must do via database)
3. **Global limit only**: Cannot set per-pool or per-permalink limits
4. **No grace period**: Limit is enforced immediately

## Documentation References

- **Architecture**: [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)
- **Patterns**: [docs/PATTERNS.md](docs/PATTERNS.md)
- **Adding Features**: [docs/ADDING_FEATURES.md](docs/ADDING_FEATURES.md)
- **Dialog Patterns**: [docs/core/DIALOG_ACTION_ROW_PATTERN.md](docs/core/DIALOG_ACTION_ROW_PATTERN.md)

---

**Implementation Status**: ✅ Complete

**Ready for Testing**: Yes

**Documentation**: This file
