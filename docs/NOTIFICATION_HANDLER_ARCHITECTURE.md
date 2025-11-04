# Notification Handler Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                     Event System (EventBus)                      │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │ Event Listeners (application/events/listeners.py)           │ │
│  │  - notify_match_scheduled()                                 │ │
│  │  - notify_tournament_created()                              │ │
│  │  - notify_crew_approved()                                   │ │
│  │  - ... (one per event type)                                 │ │
│  └─────────────────────┬──────────────────────────────────────┘ │
└────────────────────────┼────────────────────────────────────────┘
                         │ Creates NotificationLog(PENDING)
                         ↓
┌─────────────────────────────────────────────────────────────────┐
│               NotificationProcessor (Background Task)            │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │ Polls every 30 seconds for PENDING notifications            │ │
│  │  - _process_pending_notifications()                         │ │
│  │  - _dispatch_notification()                                 │ │
│  │    ├─> _handle_discord_notification()                       │ │
│  │    ├─> _handle_email_notification() [TODO]                  │ │
│  │    └─> _handle_webhook_notification() [TODO]                │ │
│  └─────────────────────┬──────────────────────────────────────┘ │
└────────────────────────┼────────────────────────────────────────┘
                         │ Calls handler.send_notification()
                         ↓
┌─────────────────────────────────────────────────────────────────┐
│                   BaseNotificationHandler (ABC)                  │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │ Abstract interface for all notification handlers            │ │
│  │                                                              │ │
│  │ @abstractmethod                                             │ │
│  │ send_notification(user, event_type, event_data)             │ │
│  │   -> (NotificationDeliveryStatus, error_message)            │ │
│  │                                                              │ │
│  │ Optional formatting hooks:                                  │ │
│  │  - format_match_scheduled(event_data)                       │ │
│  │  - format_tournament_created(event_data)                    │ │
│  │  - ... (one per event type)                                 │ │
│  └─────────────────────┬──────────────────────────────────────┘ │
└────────────────────────┼────────────────────────────────────────┘
                         │ Implemented by concrete handlers
          ┌──────────────┼──────────────┬────────────────┐
          ↓              ↓              ↓                ↓
┌──────────────────┐ ┌────────────┐ ┌──────────┐ ┌────────────┐
│ Discord Handler  │ │   Email    │ │ Webhook  │ │   SMS      │
│                  │ │  Handler   │ │ Handler  │ │  Handler   │
├──────────────────┤ │  [Future]  │ │ [Future] │ │  [Future]  │
│ send_            │ └────────────┘ └──────────┘ └────────────┘
│  notification()  │
│   ├─> Route via  │
│   │   handler_map│
│   └─> Fall back  │
│       to generic │
│                  │
│ Private methods: │
│  _send_discord_  │
│   dm()           │
│  _create_embed() │
│  _send_match_    │
│   scheduled()    │
│  _send_crew_     │
│   approved()     │
│  ... (16 total)  │
└──────────────────┘
       │
       │ Uses Discord bot
       ↓
┌──────────────────┐
│  Discord API     │
│  (discord.py)    │
│                  │
│  - Fetch user    │
│  - Send DM       │
│  - Handle errors │
│    (403, 429)    │
└──────────────────┘
```

## Data Flow

1. **Event Occurs** (e.g., match scheduled)
   - Service emits event via EventBus
   - Event listener receives event (HIGH priority for audit, NORMAL for notifications)

2. **Notification Queued**
   - Listener calls `NotificationService.queue_notification()`
   - Creates `NotificationLog` with status=PENDING
   - Saves to database

3. **Background Processing**
   - `NotificationProcessor` polls every 30 seconds
   - Fetches PENDING/RETRYING notifications
   - Dispatches to appropriate handler based on `notification_method`

4. **Handler Routing**
   - Processor calls `handler.send_notification(user, event_type, event_data)`
   - Handler routes to event-specific method via `handler_map`
   - Event method formats notification (creates embed, email template, etc.)

5. **Delivery**
   - Handler sends notification via delivery mechanism (Discord DM, email SMTP, etc.)
   - Returns `(NotificationDeliveryStatus, error_message)` tuple
   - Processor updates `NotificationLog` with result

6. **Retry Logic**
   - If status=RETRYING and retry_count < max_retries, will retry on next poll
   - If status=FAILED or exceeded retries, marked as final failure

## Handler Map Pattern

The Discord handler uses a clean dictionary-based routing pattern:

```python
handler_map = {
    NotificationEventType.MATCH_SCHEDULED: self._send_match_scheduled,
    NotificationEventType.TOURNAMENT_CREATED: self._send_tournament_created,
    # ... all 16 event types mapped to handler methods
}

handler = handler_map.get(event_type)
if handler:
    return await handler(user, event_data)  # Route to specific handler
else:
    return await self._send_generic(user, event_type, event_data)  # Fallback
```

Benefits:
- No long if/elif chains
- Easy to add new event types (just add to map)
- Type-safe method references
- Falls back gracefully for unknown events

## Extension Points

### Adding a New Event Type

1. Add enum value to `NotificationEventType` in `models/notification_subscription.py`
2. Create event listener in `application/events/listeners.py`
3. Add handler method to `DiscordNotificationHandler`:
   ```python
   async def _send_new_event(self, user: User, event_data: dict):
       embed = self._create_embed(...)
       return await self._send_discord_dm(user, message, embed)
   ```
4. Add to `handler_map` in `send_notification()` method
5. Optional: Override `format_new_event()` in base class for other handlers

### Adding a New Notification Method

1. Create new handler class extending `BaseNotificationHandler`
2. Implement `send_notification()` method
3. Add to `NotificationProcessor.__init__()`
4. Add dispatch method to `NotificationProcessor`:
   ```python
   async def _handle_new_method_notification(self, notification, user):
       status, error = await self.new_handler.send_notification(
           user, event_type, event_data
       )
       # Update notification log
   ```
5. Add routing in `_dispatch_notification()`

## Type Safety

All components are fully typed:

```python
async def send_notification(
    self,
    user: User,                              # Database model
    event_type: NotificationEventType,       # Enum
    event_data: dict                          # Event-specific data
) -> tuple[NotificationDeliveryStatus, Optional[str]]:  # (Status enum, error message)
    """Send notification - enforced by ABC."""
```

This enables:
- IDE autocomplete
- Type checking (Pylance, mypy)
- Clear contracts between components
- Catch errors at development time
