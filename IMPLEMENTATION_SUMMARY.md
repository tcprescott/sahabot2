# Async Tournament VoD Submission and Review Flagging - Implementation Summary

## Overview
This implementation adds the ability for users to submit VoD URLs and comments after completing async tournament races, as well as flag their runs for special review attention. This matches functionality from the original SahasrahBot.

## Changes Made

### 1. Database Model Updates
**File:** `models/async_tournament.py`

Added two new fields to `AsyncTournamentRace`:
- `review_requested_by_user` (BooleanField): Tracks if user flagged their run
- `review_request_reason` (TextField): Stores user's reason for review request

**Migration Required:**
```bash
poetry run aerich migrate --name "add_review_flag_fields_to_async_races"
poetry run aerich upgrade
```

### 2. API Schema Updates
**File:** `api/schemas/async_tournament.py`

- Added `review_requested_by_user` and `review_request_reason` to `AsyncTournamentRaceReviewOut`
- Created new schema `AsyncTournamentRaceUpdateRequest` for submission updates
- Schema validates that review flag requests include a reason

### 3. API Endpoint
**File:** `api/routes/async_tournaments.py`

Added new endpoint: `PATCH /api/async-tournaments/races/{race_id}/submission`
- Accepts: VoD URL, runner notes, review flag, review reason
- Authorization: Only race participant can update
- Validation: Review flag requires reason (returns 422 if missing)
- Returns: Full race details including new fields

Updated existing endpoints to include new fields in responses:
- `GET /api/async-tournaments/{tournament_id}/review-queue`
- `GET /api/async-tournaments/races/{race_id}/review`
- `PATCH /api/async-tournaments/races/{race_id}/review`

### 4. Service Layer
**File:** `application/services/tournaments/async_tournament_service.py`

Added new method: `update_race_submission()`
- Validates user is race participant
- Validates review flag requests include reason
- Updates race via repository
- Creates audit log entry
- Returns updated race or None if unauthorized

### 5. Discord Bot Views
**File:** `discordbot/async_tournament_views.py`

Added three new components:

#### RaceCompletedView
- Persistent view shown after race completion
- Two buttons: "Submit VOD & Notes" and "Flag for Review"
- Only works for race participant

#### SubmitVODModal
- Text input for VOD URL (optional)
- Long text input for runner notes (optional)
- Calls service to update race
- Shows confirmation message

#### FlagForReviewModal
- Long text input for review reason (required)
- Calls service to flag race
- Shows confirmation with flag emoji

### 6. Discord Bot Command Updates
**File:** `discordbot/commands/async_tournament.py`

- Registered `RaceCompletedView` as persistent view in `on_ready()`
- Ensures view persists across bot restarts

### 7. Review Dialog Updates
**File:** `components/dialogs/tournaments/race_review_dialog.py`

- Added warning banner: "⚠️ FLAGGED FOR REVIEW BY USER"
- Shows review request reason in yellow highlighted box
- Clearly visible when reviewing flagged runs

### 8. Review Queue Updates
**File:** `views/tournaments/async_review_queue.py`

- Added 🚩 flag emoji to review status for flagged runs
- Shows "(User Flagged)" text for pending flagged runs
- Makes flagged runs easy to identify in list

## User Workflows

### Submitting VoD After Race
1. User completes async race in Discord
2. Bot displays RaceCompletedView with two buttons
3. User clicks "Submit VOD & Notes"
4. Modal opens with two optional fields
5. User enters VoD URL and/or notes
6. Bot confirms submission in thread
7. Data saved to database and visible in web interface

### Flagging Run for Review
1. User completes async race in Discord
2. Bot displays RaceCompletedView with two buttons
3. User clicks "Flag for Review"
4. Modal opens requiring reason
5. User enters why they want review
6. Bot confirms with flag emoji
7. Run appears with 🚩 in review queue
8. Reviewers see warning banner when reviewing

### Reviewer Experience
1. Reviewer accesses review queue
2. Flagged runs show 🚩 emoji in status column
3. Reviewer opens flagged run
4. Warning banner clearly indicates user requested review
5. Review reason displayed in yellow box
6. Reviewer completes normal review process

## Security & Authorization

- API validates user is race participant before allowing updates
- Discord modals only work for race participant (user ID check)
- Service layer enforces all authorization
- Audit logs record all submission updates
- No cross-tenant data access possible

## Code Quality

- ✅ No `print()` statements (uses logger)
- ✅ No f-strings in logging (uses lazy % formatting)
- ✅ No `datetime.utcnow()` usage
- ✅ No inline imports
- ✅ External links use `new_tab=True`
- ✅ Proper async/await usage
- ✅ Docstrings on all public methods
- ✅ Type hints on parameters

## Testing

Manual testing required. See `ASYNC_VOD_SUBMISSION_TESTING.md` for comprehensive test plan covering:
- VoD submission via Discord
- Review flagging via Discord
- API endpoints for both features
- Review queue display
- Review dialog display
- Authorization checks
- Edge cases

## Original SahasrahBot Parity

The implementation matches the original bot's functionality:
- ✅ Submit VoD URL after race
- ✅ Submit runner notes/comments
- ✅ Modal-based submission interface
- ✅ Only race participant can submit
- ✅ Data stored for reviewer access

**New Features Beyond Original:**
- 🚩 Flag runs for special review attention
- 📝 Provide reason for review request
- 🎯 Visual indicators in review queue
- ⚠️ Warning banners in review dialog

## Future Enhancements

Potential improvements not in scope for this PR:
- Sort review queue by flag status
- Notifications when flagged run is reviewed
- Statistics on flag frequency
- Auto-flag based on anomalous times
- Edit VoD/notes after initial submission
- Discord command to update submission
