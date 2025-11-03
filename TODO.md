# TODO List

## Features & Enhancements

### Add Organization Setting for Manual Channel ID Input
**Priority:** Medium  
**Status:** Not Started

Implement organization-level setting to control whether manual Discord channel ID input is available in AsyncTournamentDialog.

**Steps:**
1. Add `allow_manual_channel_id` setting to organization settings model/table
2. Update `OrganizationService` to get/set this setting
3. Update `org_async_tournaments.py` to read setting and pass to dialog constructor in `_open_create_dialog` and `_open_edit_dialog` methods
4. Consider adding UI toggle in organization settings view for admins to control this flag

**Files to modify:**
- `models/organizations.py` or `models/settings.py`
- `application/services/organization_service.py`
- `views/organization/org_async_tournaments.py`
- `views/organization/org_settings.py` (if adding UI toggle)

---

## Bugs & Issues

_(None currently tracked)_

---

## Technical Debt

_(None currently tracked)_
