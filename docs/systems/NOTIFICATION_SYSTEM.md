# Notification System - Implementation Guide

## Overview

The notification system allows users to subscribe to events and receive notifications via various methods (Discord DM, Email, etc.). Currently, Discord DM is the primary implementation target.

## Architecture

### Models

**`models/notification_subscription.py`**:
- `NotificationMethod` enum: DISCORD_DM, EMAIL, WEBHOOK, SMS
- `NotificationEventType` enum: Subset of existing events (match scheduled, tournament created, invite received, etc.)
- `NotificationSubscription` model: User subscriptions to events

**`models/notification_log.py`**:
- `NotificationDeliveryStatus` enum: PENDING, SENT, FAILED, RETRYING
- `NotificationLog` model: Audit trail of all notification attempts

### Repository Layer

**`application/repositories/notification_repository.py`**:
- `create_subscription()` - Create new subscription
- `get_user_subscriptions()` - Get subscriptions for a user
- `get_subscriptions_for_event()` - Get all subscriptions for an event type
- `create_notification_log()` - Log notification attempt
- `update_notification_log()` - Update delivery status

### Service Layer

**`application/services/notification_service.py`**:
- `subscribe()` - Subscribe user to event
- `unsubscribe()` - Remove subscription
- `get_user_subscriptions()` - Get user's subscriptions
- `toggle_subscription()` - Enable/disable subscription
- `queue_notification()` - Create pending notifications based on subscriptions
- `mark_notification_sent()` - Update delivery status

## Next Steps

### 1. Discord Notification Handler
Create `application/services/notification_handlers/discord_handler.py`:
- Send Discord DMs using the Discord bot
- Handle rate limits and user DM settings
- Retry logic for failed deliveries

### 2. Event Listener
Create `application/events/listeners/notification_listener.py`:
- Listen to existing events (UserCreatedEvent, MatchScheduledEvent, etc.)
- Check for user subscriptions
- Queue notifications via NotificationService

### 3. Background Processor
Either integrate with existing TaskScheduler or create dedicated processor:
- Poll for PENDING notifications
- Dispatch to appropriate handler (Discord, Email, etc.)
- Update delivery status
- Retry failed notifications with backoff

### 4. User Interface
Create `views/user_profile/notification_preferences.py`:
- Display current subscriptions
- Add/remove subscriptions
- Toggle subscriptions on/off
- View notification history

### 5. Database Migration
```bash
poetry run aerich migrate --name "add_notification_system"
poetry run aerich upgrade
```

## Event Type Mapping

The `NotificationEventType` enum maps to existing event types:

| Notification Event | Original Event | Scope |
|-------------------|----------------|-------|
| MATCH_SCHEDULED | MatchScheduledEvent | User (participant) |
| MATCH_COMPLETED | MatchCompletedEvent | User (participant) |
| TOURNAMENT_CREATED | TournamentCreatedEvent | Organization |
| TOURNAMENT_STARTED | TournamentStartedEvent | Organization |
| INVITE_RECEIVED | InviteCreatedEvent | User (invitee) |
| USER_PERMISSION_CHANGED | UserPermissionChangedEvent | User |

## Permission Model

- **Personal Events**: User can subscribe to events that directly involve them
  - Match scheduled/completed (when user is a participant)
  - Invite received (when user is the invitee)
  - Permission changed (when it's their permission)

- **Organization Events**: User must be org member to subscribe
  - Tournament created/started/ended in their org
  - Member added/removed from their org
  
- **Organization Admin Events**: User must have org admin permission
  - All organization events
  - Member permission changes
  - Organization settings changes

## Security Considerations

1. **Subscription Validation**: Check user has permission to subscribe to event type
2. **Data Privacy**: Don't include sensitive data in notification event_data
3. **Rate Limiting**: Prevent notification spam (max per user per hour)
4. **Opt-Out**: Always provide easy unsubscribe mechanism
5. **Discord Privacy**: Check if user has DMs enabled before sending

## Testing Strategy

1. **Unit Tests**: Test subscription logic, filtering, permissions
2. **Integration Tests**: Test event → notification flow
3. **Discord Bot Tests**: Test DM sending, error handling
4. **E2E Tests**: Create event → verify notification delivered

## Future Enhancements

- Email notifications (SMTP integration)
- Webhook notifications (custom integrations)
- SMS notifications (Twilio/similar)
- Notification preferences per event type
- Digest mode (batch notifications)
- Custom notification templates
- Push notifications (mobile app)
