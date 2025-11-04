# Notification System - Implementation Complete

## Overview
The notification system is now fully implemented and integrated into SahaBot2. Users can subscribe to various events and receive notifications via Discord DMs (with email/webhook support planned).

## What's Implemented

### ✅ Database Layer
- **Models**:
  - `NotificationSubscription`: User subscriptions to events with notification method preferences
  - `NotificationLog`: Audit trail of all notification deliveries
- **Enums**:
  - `NotificationMethod`: DISCORD_DM, EMAIL, WEBHOOK, SMS
  - `NotificationEventType`: Event types users can subscribe to (100-series for users, 200-series for orgs, 300-series for tournaments, etc.)
  - `NotificationDeliveryStatus`: PENDING, SENT, FAILED, RETRYING

### ✅ Repository Layer
- `NotificationRepository`: Data access for subscriptions and notification logs
  - CRUD operations for subscriptions
  - Query subscriptions by user, event type, organization
  - Create and update notification logs
  - Get notification history for users

### ✅ Service Layer
- `NotificationService`: Business logic for managing notifications
  - `subscribe()`: Add subscription for a user
  - `unsubscribe()`: Remove subscription
  - `toggle_subscription()`: Enable/disable subscription
  - `queue_notification()`: Queue notification for a specific user
  - `queue_broadcast_notification()`: Queue notification for all subscribed users
  - `mark_notification_sent()`: Update delivery status

### ✅ Event Listeners
Event listeners automatically queue notifications when events occur:
- **Match Scheduled**: Notifies both players when a match is scheduled
- **Tournament Created**: Broadcasts to all subscribers of tournament creation events
- **Invite Received**: Notifies user when invited to an organization

### ✅ Notification Handlers
- **Discord Handler** (`DiscordNotificationHandler`):
  - Sends Discord DMs via the bot
  - Pre-built methods for common events (match scheduled, tournament created, invite received)
  - Handles rate limits, DM privacy settings, and errors
  - Returns delivery status (SENT, FAILED, RETRYING)

### ✅ Background Processor
- `NotificationProcessor`: Polls for pending notifications and dispatches them
  - Runs every 30 seconds by default
  - Processes up to 100 pending notifications per cycle
  - Retry logic with max 3 attempts
  - Routes to appropriate handler based on notification method
  - Integrated into app lifecycle (starts/stops with app)

### ✅ User Interface
- **Notification Preferences** view in user profile:
  - Add new subscriptions (event type + notification method)
  - View all current subscriptions
  - Toggle subscriptions on/off
  - Delete subscriptions
  - Accessible via Profile > Notifications

### ✅ Database Migration
- Migration created and applied: `27_20251103205647_add_notification_system.py`
- Tables: `notification_subscriptions`, `notification_logs`

## How It Works

### Flow Diagram
```
Event Occurs (e.g., Match Scheduled)
    ↓
Event Emitted (MatchScheduledEvent)
    ↓
Event Listener (notify_match_scheduled)
    ↓
NotificationService.queue_notification()
    ↓
Creates NotificationLog entries (status: PENDING)
    ↓
NotificationProcessor polls every 30s
    ↓
Dispatches to appropriate handler
    ↓
DiscordNotificationHandler.send_notification()
    ↓
Discord DM sent to user
    ↓
NotificationLog updated (status: SENT or FAILED)
```

### Multi-Tenancy Support
- Subscriptions can be organization-scoped (e.g., "notify me about tournaments in my org")
- Global subscriptions (organization=NULL) receive all events
- Organization filter uses `OR` logic: `(organization_id=X OR organization IS NULL)`

### Security & Privacy
- Users can only manage their own subscriptions
- Ownership validated in service layer (`toggle_subscription`, `unsubscribe`)
- Discord DMs respect user privacy settings (handler catches `discord.Forbidden`)
- Notification logs track all delivery attempts for auditing

## Available Event Types

| Event Type | Value | Description |
|-----------|-------|-------------|
| MATCH_SCHEDULED | 400 | User's match is scheduled |
| MATCH_COMPLETED | 401 | User's match is completed |
| TOURNAMENT_CREATED | 300 | New tournament created |
| TOURNAMENT_STARTED | 301 | Tournament has started |
| TOURNAMENT_ENDED | 302 | Tournament has ended |
| INVITE_RECEIVED | 500 | User invited to organization |

## Configuration

### Notification Processor Settings
Default settings in `NotificationProcessor`:
- Poll interval: 30 seconds
- Max retries: 3 attempts
- Batch size: 100 notifications per cycle

To customize:
```python
processor = NotificationProcessor(
    poll_interval=60,  # Check every minute
    max_retries=5,     # Retry up to 5 times
)
```

### Adding New Event Types
1. Add to `NotificationEventType` enum in `models/notification_subscription.py`
2. Add event listener in `application/events/listeners.py`
3. (Optional) Add specialized handler method in `DiscordNotificationHandler`

Example:
```python
# 1. Add enum value
class NotificationEventType(IntEnum):
    MATCH_RESCHEDULED = 402

# 2. Add listener
@EventBus.on(MatchRescheduledEvent, priority=EventPriority.NORMAL)
async def notify_match_rescheduled(event: MatchRescheduledEvent):
    # Queue notifications...

# 3. Add handler method (optional)
async def send_match_rescheduled_notification(self, user, event_data):
    embed = self.create_embed(
        title="⏰ Match Rescheduled",
        description="Your match has been rescheduled",
        # ...
    )
    return await self.send_notification(user, message, embed)
```

## Testing

### Manual Testing Steps
1. **Subscribe to an event**:
   - Go to Profile > Notifications
   - Add subscription for "Match Scheduled" via Discord DM
   
2. **Trigger the event**:
   - Create/schedule a match in a tournament
   
3. **Verify notification**:
   - Check notification_logs table (should have PENDING entry)
   - Wait 30 seconds for processor cycle
   - Check for Discord DM
   - Verify notification_log updated to SENT

### Database Queries for Debugging
```sql
-- View all pending notifications
SELECT * FROM notification_logs 
WHERE delivery_status = 0 
ORDER BY created_at DESC;

-- View user's subscriptions
SELECT * FROM notification_subscriptions 
WHERE user_id = <user_id> AND is_active = 1;

-- View notification delivery history
SELECT nl.*, u.discord_username 
FROM notification_logs nl 
JOIN users u ON nl.user_id = u.id 
ORDER BY nl.created_at DESC 
LIMIT 50;
```

## Next Steps (Future Enhancements)

### Email Handler
- Implement `EmailNotificationHandler` in `application/services/notification_handlers/`
- Use service like SendGrid or AWS SES
- Add email templates for each event type
- Handle unsubscribe links and bounce tracking

### Webhook Handler
- Implement `WebhookNotificationHandler`
- Allow users to configure webhook URLs in preferences
- Send POST requests with event data
- Handle retries for failed webhooks

### Advanced Features
- **Digest notifications**: Option to batch notifications and send once daily
- **Quiet hours**: User-configurable hours when notifications are suppressed
- **Priority levels**: Urgent vs normal notifications
- **Custom templates**: Allow users to customize notification text
- **Push notifications**: Mobile app push notifications
- **In-app notifications**: Bell icon with notification center in UI

### Performance Optimizations
- **Batching**: Send multiple Discord DMs in parallel
- **Caching**: Cache user subscription preferences
- **Queue system**: Use Redis/RabbitMQ instead of polling database
- **Rate limiting**: Global rate limit across all notification methods

## Troubleshooting

### Notifications Not Sending
1. Check if notification processor is running: Look for "Notification processor started" in logs
2. Check for pending notifications: Query `notification_logs` with `delivery_status = 0`
3. Check processor errors: Look for exceptions in logs prefixed with "Error in notification processor"
4. Verify Discord bot is running: `get_bot_instance()` should return bot instance

### User Not Receiving Discord DMs
1. Check if user has DMs enabled: Discord privacy settings
2. Check if user has blocked the bot
3. Check notification_log for error_message: May indicate "DMs disabled or bot blocked"
4. Verify user's discord_id is correct in database

### Performance Issues
1. Check number of pending notifications: Should be < 100 per cycle
2. Increase poll_interval if processing is too frequent
3. Add indexes on notification_logs: `(delivery_status, created_at)`
4. Monitor processor execution time in logs

## Files Modified/Created

### New Files
- `models/notification_subscription.py`
- `models/notification_log.py`
- `application/repositories/notification_repository.py`
- `application/services/notification_service.py`
- `application/services/notification_processor.py`
- `application/services/notification_handlers/__init__.py`
- `application/services/notification_handlers/discord_handler.py`
- `views/user_profile/notification_preferences.py`
- `docs/NOTIFICATION_SYSTEM.md` (implementation guide)
- This file: `NOTIFICATION_SYSTEM_COMPLETE.md`

### Modified Files
- `migrations/tortoise_config.py`: Added notification models to config
- `database.py`: Added notification models to Tortoise init
- `models/__init__.py`: Exported notification models and enums
- `application/events/listeners.py`: Added notification event listeners
- `main.py`: Integrated notification processor into app lifecycle
- `pages/user_profile.py`: Added notifications view to sidebar
- `views/user_profile/__init__.py`: Exported NotificationPreferencesView

## Metrics & Monitoring

To monitor notification system health:

```python
# Count pending notifications
pending_count = await NotificationLog.filter(
    delivery_status=NotificationDeliveryStatus.PENDING
).count()

# Success rate (last 24 hours)
from datetime import datetime, timezone, timedelta
yesterday = datetime.now(timezone.utc) - timedelta(days=1)

sent = await NotificationLog.filter(
    delivery_status=NotificationDeliveryStatus.SENT,
    created_at__gte=yesterday
).count()

failed = await NotificationLog.filter(
    delivery_status=NotificationDeliveryStatus.FAILED,
    created_at__gte=yesterday
).count()

success_rate = sent / (sent + failed) if (sent + failed) > 0 else 0
```

## Conclusion

The notification system is production-ready with Discord DM support. Users can subscribe to events via the Profile > Notifications page, and notifications are automatically queued and delivered when events occur. The system is extensible and ready for additional notification methods (email, webhooks) to be added in the future.
