# Async Race Review System

## Overview
The Async Race Review system allows designated users to review, approve, and edit the finish times of async tournament race submissions. This feature is crucial for maintaining the integrity of async tournaments by allowing moderators to verify race results before they're officially recorded.

## Features

### Permission-Based Access
- **ASYNC_REVIEWER**: Organization-level permission that grants access to the review queue
- **ADMIN**: Organization admins automatically have review access
- **SUPERADMIN**: Global admins have review access across all organizations

### Review Workflow
1. Users complete async races and submit their times
2. Races appear in the review queue with status "pending"
3. Reviewers can:
   - View all race details (even if tournament has `hide_results=True`)
   - Accept or reject race submissions
   - Override/correct submitted times if needed
   - Add reviewer notes for audit trail
4. Once reviewed, races are marked as "accepted" or "rejected"
5. Review metadata (reviewer, timestamp, notes) is stored for auditing

### Review Queue Interface
Located at: `/org/{organization_id}/async/{tournament_id}/review`

**Filtering Options:**
- **Race Status**: Filter by race completion status (pending, in_progress, finished, forfeit, disqualified)
- **Review Status**: Filter by review state (pending, accepted, rejected)
- **Reviewer**: Filter by who reviewed (unreviewed, all, or specific reviewer)

**Table Columns:**
- Race ID
- Player name
- Pool assignment
- Elapsed time
- Race status
- Review status
- Reviewer name
- Review action button

### Review Dialog
Each race can be opened in a detailed review dialog showing:

**Race Information:**
- Player details
- Current elapsed time
- Race status
- Pool assignment
- VOD URL (if submitted)

**Review Actions:**
- Review status selection (pending/accepted/rejected)
- Elapsed time override (optional, in HH:MM:SS format)
- Reviewer notes (free-text field for comments)
- Save or cancel buttons

## Database Schema

### AsyncTournamentRace Model Extensions
```python
review_status: str = 'pending'  # pending, accepted, rejected
reviewed_by: ForeignKey[User] = None  # Reviewer who processed this race
reviewed_at: datetime = None  # Timestamp of review
reviewer_notes: TextField = None  # Review comments/notes
```

## API Endpoints

### GET `/api/async-tournaments/{tournament_id}/review-queue`
Retrieve the review queue for a tournament.

**Query Parameters:**
- `status` (optional): Filter by race status
- `review_status` (optional): Filter by review status
- `reviewed_by_id` (optional): Filter by reviewer (-1 for unreviewed)
- `limit` (optional): Maximum results to return

**Authorization**: Requires ASYNC_REVIEWER or ADMIN permission in the organization

**Returns**: List of races with full details (bypasses hide_results)

### GET `/api/async-tournaments/races/{race_id}/review`
Get detailed review information for a specific race.

**Authorization**: Requires ASYNC_REVIEWER or ADMIN permission

**Returns**: Full race details including review metadata

### PATCH `/api/async-tournaments/races/{race_id}/review`
Update the review status of a race.

**Request Body:**
```json
{
  "review_status": "accepted",  // required: pending, accepted, rejected
  "reviewer_notes": "Time verified via VOD",  // optional
  "elapsed_time": "01:23:45"  // optional: override time in HH:MM:SS
}
```

**Authorization**: Requires ASYNC_REVIEWER or ADMIN permission

**Side Effects**:
- Updates race review metadata (status, reviewer, timestamp, notes)
- If elapsed_time provided, updates race finish time
- Records action in audit log
- Does NOT notify the user (future enhancement)

## Service Layer

### AsyncTournamentService Methods

#### `can_review_async_races(user, organization_id) -> bool`
Check if a user has permission to review races in an organization.

**Logic:**
1. Delegates to `OrganizationService.user_can_review_async_races()`
2. Checks for ADMIN permission (global or org-level)
3. Checks for ASYNC_REVIEWER org-level permission

#### `get_review_queue(user, organization_id, tournament_id, filters) -> list`
Retrieve filtered review queue for reviewers.

**Authorization**: Calls `can_review_async_races()` first
**Special Behavior**: Bypasses `hide_results` setting for authorized reviewers

#### `get_race_for_review(user, race_id, organization_id) -> dict`
Get detailed race information for review.

**Authorization**: Verifies reviewer permission and race belongs to organization

#### `update_race_review(user, race_id, organization_id, review_data) -> dict`
Process a review action (accept/reject/edit).

**Authorization**: Verifies reviewer permission
**Audit**: Logs all review actions with user, timestamp, and changes

### OrganizationService Additions

#### `user_can_review_async_races(user, organization_id) -> bool`
Helper method following the pattern of `user_can_manage_tournaments()`.

**Grants access if:**
- User is a global or org-level ADMIN, OR
- User has the ASYNC_REVIEWER org permission

## Permission Management

### Adding ASYNC_REVIEWER to a User
1. Navigate to Organization Admin → Members
2. Click on the user to edit permissions
3. Select "ASYNC_REVIEWER" from the permission dropdown
4. Save changes

### Permission Type Definition
The ASYNC_REVIEWER permission is automatically created for all new organizations via `initialize_default_permissions()`.

**Definition:**
```python
"ASYNC_REVIEWER": "Review and approve async tournament race submissions."
```

## UI Components

### AsyncReviewQueueView (`views/tournaments/async_review_queue.py`)
Main view component for the review queue.

**Features:**
- Responsive table with mobile support
- Real-time filtering
- Refresh button to reload data
- Opens RaceReviewDialog on row click

### RaceReviewDialog (`components/dialogs/tournaments/race_review_dialog.py`)
Modal dialog for reviewing individual races.

**Features:**
- Extends BaseDialog for consistent styling
- Form validation (time format: HH:MM:SS)
- Review status selection
- Optional time override
- Reviewer notes textarea
- Save/Cancel actions

## Future Enhancements
1. **Notifications**: Notify users when their races are reviewed
2. **Bulk Actions**: Accept/reject multiple races at once
3. **Review History**: Show review changelog for each race
4. **Review Statistics**: Dashboard showing review queue metrics
5. **Auto-Accept**: Configurable rules for automatic acceptance (e.g., trusted users)
6. **Review Comments**: Public vs private reviewer notes
7. **Review Disputes**: Allow users to request re-review with evidence

## Testing Checklist
- [ ] ASYNC_REVIEWER permission grants review access
- [ ] ADMIN permission grants review access
- [ ] Non-reviewers cannot access review endpoints
- [ ] Review queue respects organization boundaries
- [ ] Hide results is bypassed for reviewers
- [ ] Time override updates race correctly
- [ ] Review actions are audited
- [ ] Filtering works correctly
- [ ] Mobile responsive design works
- [ ] Dialog validation works (time format)
- [ ] Permission initialization on org creation
- [ ] API rate limiting enforced
- [ ] Unauthorized access returns empty results (not errors)

## Migration Notes
Database migration `17_20251103012605_add_async_race_review_fields.py` adds:
- `reviewed_by_id` (BIGINT, nullable, FK to users)
- `reviewer_notes` (LONGTEXT, nullable)
- `review_status` (VARCHAR(20), default 'pending')
- `reviewed_at` (DATETIME(6), nullable)

Run migration with:
```bash
poetry run aerich upgrade
```
