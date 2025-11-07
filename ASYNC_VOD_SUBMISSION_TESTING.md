# Async Tournament VoD Submission Testing Guide

## Overview
This document outlines the manual testing steps for the new VoD submission and review flagging features.

## Prerequisites
1. Run database migration: `poetry run aerich migrate --name "add_review_flag_fields_to_async_races"`
2. Apply migration: `poetry run aerich upgrade`
3. Have an async tournament configured with a Discord channel
4. Have at least one permalink/seed available in a pool

## Features to Test

### 1. VoD and Notes Submission via Discord

**Steps:**
1. Start a new async run in Discord
2. Complete the race (click Ready, wait for countdown, click Finish)
3. After finishing, verify you see two buttons:
   - "Submit VOD & Notes" (green, 🗒️ emoji)
   - "Flag for Review" (blue, 🚩 emoji)
4. Click "Submit VOD & Notes"
5. In the modal, enter:
   - VOD URL (e.g., https://www.twitch.tv/videos/123456)
   - Runner notes (any text)
6. Submit the modal
7. Verify confirmation message appears in the thread
8. Check web interface to confirm VOD URL and notes are saved

**Expected Results:**
- Both buttons appear after race completion
- Modal opens with two input fields
- Submission succeeds and shows confirmation
- Data is visible in web interface

### 2. Flag for Review via Discord

**Steps:**
1. Complete a race (or use existing completed race)
2. Click "Flag for Review" button
3. In the modal, enter a reason (e.g., "I think my time is incorrect")
4. Submit the modal
5. Verify confirmation message with flag emoji appears
6. Check review queue in web interface

**Expected Results:**
- Modal requires reason to be entered
- Submission succeeds with confirmation
- Run appears in review queue with 🚩 flag indicator
- Review queue shows "(User Flagged)" text for pending runs

### 3. VoD Submission via API

**Steps:**
1. Use API client (Swagger UI or curl) to call:
   ```
   PATCH /api/async-tournaments/races/{race_id}/submission?organization_id={org_id}
   ```
2. Send JSON body:
   ```json
   {
     "runner_vod_url": "https://www.youtube.com/watch?v=example",
     "runner_notes": "This is a test submission"
   }
   ```
3. Verify response shows updated race data

**Expected Results:**
- API accepts the request
- Returns 200 with updated race data
- Changes are reflected in database

### 4. Review Flag via API

**Steps:**
1. Call the same API endpoint with:
   ```json
   {
     "review_requested_by_user": true,
     "review_request_reason": "Please review my run - timer may have been off"
   }
   ```
2. Verify response includes flag fields

**Expected Results:**
- API accepts the request
- Requires reason when flagging
- Returns 422 if flag is true but reason is missing
- Changes are reflected in review queue

### 5. Review Queue Display

**Steps:**
1. Navigate to async tournament review queue in web interface
2. Filter for pending reviews
3. Look for runs with 🚩 flag indicator
4. Verify "(User Flagged)" text appears for flagged runs
5. Open a flagged run for review

**Expected Results:**
- Flagged runs show 🚩 emoji in review status column
- Text indicates "(User Flagged)" for pending flagged runs
- Runs are easily distinguishable from non-flagged runs

### 6. Review Dialog

**Steps:**
1. Open a flagged run in the review dialog
2. Verify warning banner appears at top
3. Check that review request reason is displayed
4. Complete the review normally

**Expected Results:**
- "⚠️ FLAGGED FOR REVIEW BY USER" warning appears
- Reason text is shown in yellow highlighted box
- Review can be completed normally
- All standard review fields are available

### 7. Authorization Checks

**Steps:**
1. Try to update someone else's race submission via API
2. Try to flag someone else's race via Discord

**Expected Results:**
- API returns 404 (not found/unauthorized)
- Discord buttons only work for race participant
- Audit logs record all actions

## Edge Cases to Test

1. **Empty Submissions**
   - Submit VOD modal with both fields empty
   - Should succeed (both fields are optional)

2. **Flag Without Reason**
   - Try to flag via API without reason
   - Should return 422 error
   - Discord modal requires reason field

3. **Multiple Submissions**
   - Submit VOD multiple times
   - Each submission should update the previous values
   - Audit logs should record each update

4. **Concurrent Access**
   - Have race participant update via Discord
   - Have same user update via web interface
   - Both should work independently

## Database Verification

After testing, verify in database:
```sql
SELECT 
    id,
    user_id,
    runner_vod_url,
    runner_notes,
    review_requested_by_user,
    review_request_reason,
    review_status
FROM async_tournament_races
WHERE id = {race_id};
```

## Clean Up

After testing:
1. Review audit logs to ensure all actions were recorded
2. Check that events were emitted properly
3. Verify notification system (if applicable) sent notifications for flagged runs

## Known Limitations

1. No migration file included - user must run `aerich migrate` to generate it
2. No automated tests - manual testing required
3. Discord bot must be restarted to load new persistent views
4. Review queue doesn't support sorting by flag status (future enhancement)
