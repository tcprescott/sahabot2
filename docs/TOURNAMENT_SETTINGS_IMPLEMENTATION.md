# Tournament Settings Submission Forms - Implementation Complete

## Overview

This implementation provides a complete system for tournament players to submit race settings before their matches. The feature enables tournament automation by allowing players to configure their game settings in advance, which can then be automatically applied when creating race rooms.

## Architecture

The implementation follows SahaBot2's four-layer architecture:

```
UI Layer (pages/tournament_match_settings.py)
    ↓
Service Layer (application/services/tournaments/tournament_match_settings_service.py)
    ↓
Repository Layer (application/repositories/tournament_match_settings_repository.py)
    ↓
Model Layer (models/tournament_match_settings.py)
```

## Components

### 1. Database Model

**File**: `models/tournament_match_settings.py`

The `TournamentMatchSettings` model stores:
- Match reference (foreign key)
- Game number (1-10, for best-of-N series)
- Settings data (flexible JSON structure)
- Submission metadata (submitted_by, submitted_at)
- Validation status (is_valid, validation_error)
- Application tracking (applied, applied_at)
- Optional notes from submitter

**Constraints**:
- Unique constraint on (match, game_number) - one submission per game

### 2. Repository Layer

**File**: `application/repositories/tournament_match_settings_repository.py`

Provides data access methods:
- `get_by_id()` - Get submission by ID
- `get_for_match_and_game()` - Get submission for specific match/game
- `list_for_match()` - List all submissions for a match
- `list_for_tournament()` - List submissions for entire tournament
- `create()` - Create new submission
- `update()` - Update existing submission
- `delete()` - Delete submission
- `mark_applied()` - Mark settings as used
- `exists_for_match_and_game()` - Check existence

### 3. Service Layer

**File**: `application/services/tournaments/tournament_match_settings_service.py`

Business logic and authorization:
- **Authorization**: Players in match OR tournament managers can submit/view
- **Validation**: Basic settings structure validation (extensible)
- **Event Emission**: Emits `TournamentMatchSettingsSubmittedEvent` on submission
- **Methods**:
  - `submit_settings()` - Submit or update settings
  - `get_submission()` - Get settings (with auth check)
  - `list_submissions_for_match()` - List settings (with auth check)
  - `delete_submission()` - Delete settings (with auth check)
  - `mark_settings_applied()` - Mark as applied (for automation)
  - `validate_settings()` - Validate settings structure

### 4. API Endpoints

**File**: `api/routes/tournament_match_settings.py`

RESTful API endpoints:
- `GET /api/tournaments/settings/matches/{match_id}` - List all settings for match
- `GET /api/tournaments/settings/matches/{match_id}/game/{game_number}` - Get specific game settings
- `POST /api/tournaments/settings/matches/{match_id}` - Submit settings
- `DELETE /api/tournaments/settings/{submission_id}` - Delete submission
- `POST /api/tournaments/settings/validate` - Validate settings

**Schemas** (in `api/schemas/tournament.py`):
- `TournamentMatchSettingsOut` - Output schema
- `TournamentMatchSettingsListResponse` - List response
- `TournamentMatchSettingsSubmitRequest` - Submit request
- `TournamentMatchSettingsValidateRequest/Response` - Validation

### 5. Web UI

**File**: `pages/tournament_match_settings.py`

User interface at `/tournaments/matches/{match_id}/submit`:
- JSON editor for settings input
- Game number selector (1-10)
- Notes field for comments
- Pre-fills with existing submission
- Shows current submission info
- Real-time validation feedback
- Mobile-responsive design

### 6. Event System Integration

**Files**: 
- `application/events/types.py` - Event definition
- `application/events/listeners.py` - Event handlers
- `models/notification_subscription.py` - Notification event type

**Event**: `TournamentMatchSettingsSubmittedEvent`
- Contains: match_id, tournament_id, game_number, settings_data, submitted_by_user_id
- Triggers audit logging
- Triggers Discord notifications to other match participants

**Notification Event Type**: `MATCH_SETTINGS_SUBMITTED = 404`

## Usage

### For Players

1. Navigate to `/tournaments/matches/{match_id}/submit`
2. Select game number (if best-of-N series)
3. Enter settings in JSON format, e.g.:
   ```json
   {
     "preset": "standard",
     "mode": "open",
     "difficulty": "hard"
   }
   ```
4. Optionally add notes for tournament admins
5. Click "Submit Settings"

### For Tournament Admins

**Viewing Submissions** (via API):
```
GET /api/tournaments/settings/matches/{match_id}
```

**Marking as Applied** (in race room creation code):
```python
service = TournamentMatchSettingsService()
submission = await service.get_submission(user, match_id, game_number)
if submission:
    # Use submission.settings to configure race
    await service.mark_settings_applied(submission.id)
```

## Authorization Model

Access is granted to:
1. **Players in the match** - Can submit and view settings for their matches
2. **Tournament managers** - Can submit, view, and delete any settings in their tournament

Authorization is enforced at the service layer using the new authorization framework:
```python
# Check if user is player
is_player = await MatchPlayers.filter(match_id=match.id, user_id=user.id).exists()

# Check if user is tournament manager
can_manage = await self.auth.can(
    user,
    action=self.auth.get_action_for_operation("tournament", "update"),
    resource=self.auth.get_resource_identifier("tournament", str(tournament.id)),
    organization_id=organization_id
)
```

## Notification System

When settings are submitted:

1. **Audit Log Entry** created with:
   - Action: "tournament_match_settings_submitted"
   - Details: match_id, tournament_id, game_number, settings
   - User: submitter

2. **Discord Notifications** sent to:
   - All match participants except the submitter
   - Notification includes settings summary and submission URL

3. **Settings Summary** formatted for readability:
   - Extracts common fields (preset, mode, difficulty)
   - Falls back to settings count

## Multi-Tenant Isolation

All operations respect organization boundaries:
- Settings queries filter by match → tournament → organization
- Authorization checks verify organization membership
- Events include organization_id for proper scoping
- Audit logs scoped to organization

## Security

- **CodeQL Scan**: 0 security alerts
- **Code Review**: All issues addressed
- **Authorization**: Service-layer enforcement
- **Input Validation**: JSON parsing with error handling
- **SQL Injection**: Protected by Tortoise ORM
- **XSS**: Protected by NiceGUI framework

## Future Enhancements

### Phase 6: Tournament Integration
- Link submissions to race room creation workflow
- Auto-apply settings when creating RaceTime.gg rooms
- Update match management UI to show submission status

### Advanced Validation
- Tournament-type-specific validation rules
- Preset existence validation
- Settings compatibility checks

### Testing
- Unit tests for repository layer
- Unit tests for service layer
- API integration tests
- UI end-to-end tests

### Documentation
- User guide for players
- Admin guide for tournament managers
- API documentation

## Database Migration

**NOTE**: Migration file not yet created due to aerich not being available in current environment.

To create migration:
```bash
poetry run aerich migrate --name "add_tournament_match_settings"
poetry run aerich upgrade
```

The migration will create the `tournament_match_settings` table with:
- Primary key: id
- Foreign keys: match_id, submitted_by_id
- Fields: game_number, settings (JSON), notes, submitted, is_valid, validation_error, applied, applied_at
- Timestamps: submitted_at, updated_at
- Unique constraint: (match_id, game_number)

## Files Modified/Created

### Created Files
1. `models/tournament_match_settings.py` - Model definition
2. `application/repositories/tournament_match_settings_repository.py` - Data access
3. `application/services/tournaments/tournament_match_settings_service.py` - Business logic
4. `api/routes/tournament_match_settings.py` - API endpoints
5. `pages/tournament_match_settings.py` - Web UI
6. `docs/TOURNAMENT_SETTINGS_IMPLEMENTATION.md` - This document

### Modified Files
1. `models/__init__.py` - Export TournamentMatchSettings
2. `models/match_schedule.py` - Add reverse relation
3. `models/user.py` - Add reverse relation
4. `models/notification_subscription.py` - Add notification event type
5. `application/events/types.py` - Add event type
6. `application/events/__init__.py` - Export event type
7. `application/events/listeners.py` - Add event handlers
8. `api/schemas/tournament.py` - Add schemas
9. `frontend.py` - Register page

## Related Features

This implementation can be extended to support:
- **SahasrahBot Tournament Types**:
  - ALTTPR League (preset selection)
  - ALTTPR French Community (custom settings)
  - ALTTPR Spanish Community (preset selection)
  - SMZ3 tournaments (preset selection)
  - SM Randomizer League (preset + game selection)

- **Automated Workflows**:
  - SpeedGaming integration (episode-based submissions)
  - Deadline enforcement
  - Reminder notifications
  - Auto-race creation with submitted settings

## Support

For questions or issues:
1. Check audit logs for debugging
2. Review notification logs for delivery status
3. Use API endpoints for programmatic access
4. Check authorization service for permission issues

---

**Implementation Date**: November 6, 2025
**Status**: Complete (pending database migration)
**Next Steps**: Create migration, test in running server, add to match management UI
