# Notification Handler Refactoring

## Overview
Refactored the notification handler system to use an abstract base class pattern, making it easier to add new notification delivery methods (email, webhooks, SMS, etc.) in the future.

## Implementation Date
2025-11-03

## Architecture

### Base Class Pattern

```
BaseNotificationHandler (ABC)
    ├── send_notification(user, event_type, event_data) -> (status, error)
    │   - Abstract method that subclasses must implement
    │   - Routes to event-specific formatting/delivery logic
    │
    └── format_*() methods (optional overrides)
        - format_match_scheduled(event_data)
        - format_tournament_created(event_data)
        - ... (one for each NotificationEventType)

DiscordNotificationHandler (extends BaseNotificationHandler)
    ├── send_notification(user, event_type, event_data)
    │   - Routes to private _send_* methods via handler_map
    │   - Falls back to generic text notification if no handler exists
    │
    ├── _send_discord_dm(user, message, embed=None)
    │   - Low-level Discord DM sending with error handling
    │   - Handles rate limits, permission errors, etc.
    │
    ├── _create_embed(title, description, color, fields, ...)
    │   - Creates formatted Discord embeds
    │
    └── _send_*() methods (one per event type)
        - _send_match_scheduled(user, event_data)
        - _send_tournament_created(user, event_data)
        - _send_crew_approved(user, event_data)
        - ... (16 total handlers)
```

## Files Modified

### 1. Created `application/services/notification_handlers/base_handler.py`
New abstract base class for all notification handlers.

**Key Components:**
- `send_notification()` - Abstract method defining the interface
- `format_*()` methods - Optional hooks for subclasses to customize formatting
- Fully typed with `User`, `NotificationEventType`, `NotificationDeliveryStatus`

**Benefits:**
- Enforces consistent interface across all handlers
- Makes it easy to add email, webhook, or other notification methods
- Provides optional formatting hooks for flexibility

### 2. Refactored `application/services/notification_handlers/discord_handler.py`
Updated to extend `BaseNotificationHandler` with cleaner architecture.

**Changes:**
- Now extends `BaseNotificationHandler`
- Implements abstract `send_notification(user, event_type, event_data)` method
- Routes to specific handlers via `handler_map` dictionary
- All event-specific methods renamed to private (prefix with `_`):
  - `send_match_scheduled_notification()` → `_send_match_scheduled()`
  - `send_tournament_created_notification()` → `_send_tournament_created()`
  - etc.
- Helper methods also made private:
  - `create_embed()` → `_create_embed()`
  - Original `send_notification()` → `_send_discord_dm()` (low-level Discord sending)

**Handler Map Pattern:**
```python
handler_map = {
    NotificationEventType.MATCH_SCHEDULED: self._send_match_scheduled,
    NotificationEventType.TOURNAMENT_CREATED: self._send_tournament_created,
    # ... all 16 event types
}

handler = handler_map.get(event_type)
if handler:
    return await handler(user, event_data)
else:
    # Generic fallback
    return await self._send_discord_dm(user, f"Notification: {event_type.name}")
```

### 3. Simplified `application/services/notification_processor.py`
Updated to use the new handler interface.

**Before:**
```python
# Had to manually route to specific handler methods
if event_type == NotificationEventType.MATCH_SCHEDULED:
    status, error = await self.discord_handler.send_match_scheduled_notification(user, event_data)
elif event_type == NotificationEventType.TOURNAMENT_CREATED:
    status, error = await self.discord_handler.send_tournament_created_notification(user, event_data)
# ... repeated for all event types
```

**After:**
```python
# Single call, handler routes internally
status, error = await self.discord_handler.send_notification(user, event_type, event_data)
```

**Benefits:**
- Much cleaner and more maintainable
- No need to update processor when adding new event types
- Routing logic belongs in the handler, not the processor

### 4. Updated `application/services/notification_handlers/__init__.py`
Added export of `BaseNotificationHandler`.

## Adding New Notification Methods

The refactoring makes it trivial to add new notification delivery methods:

### Example: Email Notification Handler

```python
from application.services.notification_handlers.base_handler import BaseNotificationHandler
from models import User
from models.notification_log import NotificationDeliveryStatus
from models.notification_subscription import NotificationEventType

class EmailNotificationHandler(BaseNotificationHandler):
    """Handler for sending notifications via email."""

    def __init__(self, smtp_config):
        self.smtp = smtp_config

    async def send_notification(
        self,
        user: User,
        event_type: NotificationEventType,
        event_data: dict
    ) -> tuple[NotificationDeliveryStatus, Optional[str]]:
        """Send email notification."""
        # Format email based on event type
        subject, body = self._format_email(event_type, event_data)
        
        # Send via SMTP
        try:
            await self._send_email(user.discord_email, subject, body)
            return (NotificationDeliveryStatus.SENT, None)
        except Exception as e:
            return (NotificationDeliveryStatus.FAILED, str(e))

    def _format_email(self, event_type, event_data):
        """Format email subject and body based on event type."""
        # ... formatting logic
        pass

    async def _send_email(self, to_address, subject, body):
        """Send email via SMTP."""
        # ... SMTP sending logic
        pass
```

### Example: Webhook Notification Handler

```python
class WebhookNotificationHandler(BaseNotificationHandler):
    """Handler for sending notifications via webhooks."""

    def __init__(self, webhook_url):
        self.webhook_url = webhook_url

    async def send_notification(
        self,
        user: User,
        event_type: NotificationEventType,
        event_data: dict
    ) -> tuple[NotificationDeliveryStatus, Optional[str]]:
        """Send webhook notification."""
        payload = {
            'user_id': user.id,
            'event_type': event_type.name,
            'event_data': event_data,
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(self.webhook_url, json=payload) as resp:
                    if resp.status == 200:
                        return (NotificationDeliveryStatus.SENT, None)
                    else:
                        return (NotificationDeliveryStatus.FAILED, f"HTTP {resp.status}")
        except Exception as e:
            return (NotificationDeliveryStatus.FAILED, str(e))
```

Then update `notification_processor.py` to instantiate and use the new handler:

```python
class NotificationProcessor:
    def __init__(self):
        self.discord_handler = DiscordNotificationHandler()
        self.email_handler = EmailNotificationHandler(smtp_config)
        self.webhook_handler = WebhookNotificationHandler(webhook_url)

    async def _dispatch_notification(self, notification: NotificationLog):
        # ... existing code ...
        
        elif notification.notification_method == NotificationMethod.EMAIL:
            await self._handle_email_notification(notification, notification.user)
        elif notification.notification_method == NotificationMethod.WEBHOOK:
            await self._handle_webhook_notification(notification, notification.user)

    async def _handle_email_notification(self, notification, user):
        """Handle email notification."""
        event_type = NotificationEventType(notification.event_type)
        event_data = notification.event_data or {}
        
        status, error = await self.email_handler.send_notification(
            user, event_type, event_data
        )
        
        notification.delivery_status = status
        notification.error_message = error
        # ... save notification ...
```

## Benefits of This Architecture

### 1. Separation of Concerns
- **Base class**: Defines interface and optional formatting hooks
- **Handler classes**: Implement specific delivery mechanisms
- **Processor**: Coordinates notification dispatch, doesn't know delivery details

### 2. Extensibility
- Adding new notification methods requires only:
  1. Create new handler class extending `BaseNotificationHandler`
  2. Implement `send_notification()` method
  3. Register in processor
- No changes needed to existing handlers or event system

### 3. Testability
- Each handler can be tested independently
- Mock the base class for testing processor
- Mock the delivery mechanism for testing handlers

### 4. Maintainability
- Event-specific logic encapsulated in handler methods
- Routing logic in one place (handler_map)
- Clear, consistent naming conventions

### 5. Type Safety
- All methods fully typed
- Abstract base class enforces interface compliance
- IDE autocomplete and type checking work properly

## Migration Notes

No breaking changes for existing code:
- Event listeners still emit events the same way
- Notification processor still polls and dispatches
- Discord notifications still work identically
- All existing functionality preserved

Only internal implementation changed:
- Handler interface standardized
- Method names made private (implementation detail)
- Routing moved into handler class

## Testing Recommendations

1. **Test base class interface**:
   - Verify abstract method enforcement
   - Test format_* method defaults

2. **Test Discord handler**:
   - All 16 event types route correctly
   - Fallback works for unknown events
   - Error handling preserved (rate limits, DM disabled, etc.)

3. **Test processor integration**:
   - Notifications dispatch via new interface
   - All event types still deliver successfully
   - Status tracking works correctly

4. **Test future handlers**:
   - Email handler sends proper emails
   - Webhook handler POSTs correct payload
   - Error handling consistent across handlers

## Related Documentation

- `docs/NOTIFICATION_SYSTEM.md` - Overall notification system architecture
- `DISCORD_NOTIFICATION_HANDLERS.md` - Discord-specific handler details
- `models/notification_subscription.py` - Event types and subscription model
- `application/events/listeners.py` - Event listeners that queue notifications

## Future Enhancements

- [ ] Add email notification handler
- [ ] Add webhook notification handler
- [ ] Add SMS notification handler (Twilio)
- [ ] Add in-app notification handler (UI toast/banner)
- [ ] Add batch notification support (daily digest emails)
- [ ] Add notification preferences per delivery method
- [ ] Add template system for email formatting
- [ ] Add retry strategies per handler type
