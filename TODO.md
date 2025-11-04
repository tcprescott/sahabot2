# TODO List

## Recently Completed ✅

### Event System Implementation
**Completed:** 2025-11-03  
**Priority:** High

Implemented comprehensive event-driven architecture for asynchronous notifications, audit logging, and cross-cutting concerns.

**What was delivered:**
- ✅ Core event system (`application/events/`)
  - Base event classes with automatic metadata
  - EventBus singleton with priority support
  - 24 pre-defined event types for all major operations
  - Automatic audit logging listeners
- ✅ Integration with application
  - Auto-registration on startup
  - Example integration in UserService
  - Events emitted for user creation and permission changes
- ✅ Complete documentation (4 guides)
  - `EVENT_SYSTEM.md` - Comprehensive architecture guide
  - `EVENT_SYSTEM_EXAMPLES.md` - Real-world code examples
  - `EVENT_SYSTEM_QUICK_REFERENCE.md` - Quick reference
  - `EVENT_SYSTEM_IMPLEMENTATION.md` - Implementation summary
- ✅ Full test suite (12 tests, all passing)

**Next steps for event system:**
- Add events to remaining service methods
- Implement Discord notification handlers
- Build notification preferences UI
- Add email notifications

**Documentation:** See `docs/EVENT_SYSTEM.md` and `docs/EVENT_SYSTEM_QUICK_REFERENCE.md`

---

## Features & Enhancements

### Discord Notification System (NEW)
**Priority:** High  
**Status:** Not Started  
**Depends on:** Event System ✅

Build notification handlers that respond to events and send Discord messages.

**Steps:**
1. Create `application/events/notification_handlers.py`
2. Register handlers for tournament/race events
3. Implement Discord DM notifications
4. Implement Discord channel announcements
5. Add user notification preferences model
6. Build UI for notification preferences

**Files to create/modify:**
- `application/events/notification_handlers.py` (new)
- `models/notification_preferences.py` (new)
- `application/services/notification_service.py` (new)
- `views/user_profile/profile_notifications.py` (new)

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
