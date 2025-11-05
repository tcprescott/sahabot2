# Discord Notification Handlers - Implementation Summary

## Overview
All notification event types now have dedicated Discord DM handlers with formatted embeds. The notification processor routes each event type to its specific handler for a polished user experience.

## Implementation Date
2025-01-XX

## Files Modified

### 1. `application/services/notification_handlers/discord_handler.py`
Added 13 new handler methods with formatted Discord embeds:

#### Crew Events
- `send_crew_approved_notification()` - Notifies when user is approved for crew role (supports auto-approval)
- `send_crew_removed_notification()` - Notifies when user is removed from crew role

#### Race Events
- `send_race_submitted_notification()` - Confirms race result submission
- `send_race_approved_notification()` - Notifies when race result is approved
- `send_race_rejected_notification()` - Notifies when race result is rejected (includes reason)

#### Match Events
- `send_match_completed_notification()` - Notifies when match is completed (includes winner)

#### Tournament Events
- `send_tournament_started_notification()` - Notifies when tournament begins
- `send_tournament_ended_notification()` - Notifies when tournament concludes (includes winner)
- `send_tournament_updated_notification()` - Notifies when tournament details change

#### Organization Events
- `send_organization_member_added_notification()` - Notifies when added to organization
- `send_organization_member_removed_notification()` - Notifies when removed from organization
- `send_organization_permission_changed_notification()` - Notifies when organization permissions change

#### Permission Events
- `send_user_permission_changed_notification()` - Notifies when global permissions change

### 2. `application/services/notification_processor.py`
Updated `_handle_discord_notification()` method:

**Before:**
- Used if/elif chain for 3 event types
- Generic fallback for all other events

**After:**
- Uses `handler_map` dictionary for clean routing
- All 16 notification event types route to dedicated handlers
- Generic fallback only for truly unhandled event types (future-proofing)

## Event Type Coverage

All notification event types now have dedicated handlers:

| Event Type | Handler Method | Color | Icon |
|------------|---------------|-------|------|
| MATCH_SCHEDULED | `send_match_scheduled_notification` | Blue | 🗓️ |
| MATCH_COMPLETED | `send_match_completed_notification` | Gold | 🏆 |
| TOURNAMENT_CREATED | `send_tournament_created_notification` | Green | 🎮 |
| TOURNAMENT_STARTED | `send_tournament_started_notification` | Green | 🎮 |
| TOURNAMENT_ENDED | `send_tournament_ended_notification` | Purple | 🏁 |
| TOURNAMENT_UPDATED | `send_tournament_updated_notification` | Orange | 📝 |
| RACE_SUBMITTED | `send_race_submitted_notification` | Blue | 🏁 |
| RACE_APPROVED | `send_race_approved_notification` | Green | ✅ |
| RACE_REJECTED | `send_race_rejected_notification` | Red | ❌ |
| CREW_APPROVED | `send_crew_approved_notification` | Green | ✅/🎬 |
| CREW_REMOVED | `send_crew_removed_notification` | Red | ❌ |
| INVITE_RECEIVED | `send_invite_received_notification` | Blue | 📨 |
| ORGANIZATION_MEMBER_ADDED | `send_organization_member_added_notification` | Blue | 👥 |
| ORGANIZATION_MEMBER_REMOVED | `send_organization_member_removed_notification` | Red | 👋 |
| ORGANIZATION_PERMISSION_CHANGED | `send_organization_permission_changed_notification` | Blue | 🔐 |
| USER_PERMISSION_CHANGED | `send_user_permission_changed_notification` | Blue | 🔐 |

## Handler Design Patterns

### Common Structure
Each handler follows a consistent pattern:

```python
async def send_[event]_notification(
    self,
    user: User,
    event_data: dict
) -> tuple[NotificationDeliveryStatus, Optional[str]]:
    """
    Send a [event] notification.

    Args:
        user: User to notify
        event_data: Event data with [entity] details

    Returns:
        Tuple of (delivery_status, error_message)
    """
    # Extract event-specific data
    # Create formatted embed with appropriate color and fields
    # Send notification via base send_notification() method
```

### Embed Color Scheme
- **Green** - Positive events (approved, started, added)
- **Red** - Negative events (rejected, removed)
- **Blue** - Informational (submitted, scheduled, invited)
- **Gold/Purple** - Completion (match/tournament ended)
- **Orange** - Updates/changes

### Field Organization
- **Important fields**: Inline (True) for compact display
- **Descriptive fields**: Full-width (False) for readability
- **Footer**: Context-appropriate guidance or next steps

## Event Data Requirements

Each event type expects specific fields in `event_data`:

### Match Events
```python
{
    'match_id': int,
    'tournament_id': int,
    'scheduled_at': str,
    'opponent': str,  # For MATCH_SCHEDULED
    'winner': str,    # For MATCH_COMPLETED
}
```

### Race Events
```python
{
    'tournament_id': int,
    'time_seconds': str,
    'reviewer': str,   # For APPROVED/REJECTED
    'reason': str,     # For REJECTED
}
```

### Crew Events
```python
{
    'match_id': int,
    'role': str,
    'auto_approved': bool,   # For APPROVED
    'added_by': str,         # If auto-approved
    'approved_by': str,      # If manually approved
}
```

### Tournament Events
```python
{
    'tournament_name': str,
    'winner': str,           # For ENDED
    'changed_fields': list,  # For UPDATED
}
```

### Organization Events
```python
{
    'organization_name': str,
    'added_by': str,         # For MEMBER_ADDED
    'removed_by': str,       # For MEMBER_REMOVED
    'old_permission': str,   # For PERMISSION_CHANGED
    'new_permission': str,   # For PERMISSION_CHANGED
    'changed_by': str,       # For PERMISSION_CHANGED
}
```

### Permission Events
```python
{
    'old_permission': str,
    'new_permission': str,
    'changed_by': str,
}
```

## Error Handling

All handlers use the base `send_notification()` method which handles:
- Discord bot availability checks
- User lookup by Discord ID
- Rate limiting (429 errors)
- Permission errors (403 - DMs disabled)
- Generic HTTP exceptions

Delivery status is automatically tracked:
- `SENT` - Successfully delivered
- `FAILED` - Delivery failed (with error message)

## Testing Recommendations

1. **Create subscriptions** for each event type via `/profile?view=notifications`
2. **Trigger events** through normal app workflows:
   - Schedule/complete matches
   - Submit/review races
   - Add/remove crew members
   - Start/end tournaments
   - Manage organization memberships
   - Update permissions
3. **Check Discord DMs** for formatted embeds
4. **Verify notification logs** in database for delivery status

## Future Enhancements

- [ ] Add thumbnail images to embeds (tournament logos, user avatars)
- [ ] Include action buttons for quick responses (Accept/Decline invites)
- [ ] Add match links that deep-link to the match page
- [ ] Implement notification batching (daily digest option)
- [ ] Add rich presence for tournament participants
- [ ] Support custom embed colors per organization

## Related Files

- `models/notification_subscription.py` - Event type enum and subscription model
- `application/events/listeners.py` - Event listeners that queue notifications
- `application/services/notification_service.py` - Service layer for notification management
- `views/user_profile/notification_preferences.py` - UI for managing subscriptions
- `docs/NOTIFICATION_SYSTEM.md` - Overall notification system documentation

## Notes

- All handlers use semantic emojis and color-coding for quick visual recognition
- Embeds are mobile-friendly and respect Discord's character limits
- Generic fallback remains for any future event types not yet implemented
- Handler map pattern makes it easy to add new handlers without modifying routing logic
