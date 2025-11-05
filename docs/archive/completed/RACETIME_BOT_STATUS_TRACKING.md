# RaceTime Bot Status Tracking

## Overview

The RaceTime bot system now includes comprehensive status tracking to monitor bot health and connection state in real-time. This feature allows administrators to quickly identify and troubleshoot issues with bot credentials, network connectivity, or RaceTime.gg service availability.

## Status States

Bots can be in one of five status states:

| Status | Value | Icon | Description |
|--------|-------|------|-------------|
| **UNKNOWN** | 0 | `help` | Initial state; bot has not yet attempted to connect |
| **CONNECTED** | 1 | `check_circle` | Bot is successfully connected and operational |
| **AUTH_FAILED** | 2 | `key_off` | Authentication failed (invalid credentials) |
| **CONNECTION_ERROR** | 3 | `error` | Network or service connectivity issues |
| **DISCONNECTED** | 4 | `cloud_off` | Bot was manually stopped |

## Database Schema

### New Fields in `RacetimeBot` Model

```python
class RacetimeBot(Model):
    # ... existing fields ...
    
    # Status tracking fields
    status: IntEnumField = IntEnumField(BotStatus, default=BotStatus.UNKNOWN)
    status_message: TextField = TextField(null=True)  # Error details
    last_connected_at: DatetimeField = DatetimeField(null=True)  # Last successful connection
    last_status_check_at: DatetimeField = DatetimeField(null=True)  # Last status update
```

### Helper Methods

```python
def get_status_display(self) -> str:
    """Get human-readable status name."""
    
def is_healthy(self) -> bool:
    """Check if bot is in healthy state (CONNECTED)."""
```

## Repository Methods

### Status Update Methods

The `RacetimeBotRepository` provides several methods for tracking bot status:

```python
# Update bot status with optional message
await repository.update_bot_status(bot_id, BotStatus.CONNECTED, status_message=None)

# Record successful connection (sets status to CONNECTED)
await repository.record_connection_success(bot_id)

# Record connection failure with error details
await repository.record_connection_failure(bot_id, "Invalid OAuth credentials", BotStatus.AUTH_FAILED)

# Get all bots with non-healthy status
unhealthy_bots = await repository.get_unhealthy_bots()
```

## Automatic Status Tracking

Status is automatically tracked during bot lifecycle:

### On Bot Start

When a bot starts (`racetime/client.py::start_racetime_bot`):
1. Bot instance is created with `bot_id` parameter
2. Background task wraps the bot's `run()` method
3. On successful start, status is set to **CONNECTED**
4. If startup fails:
   - Authentication errors → **AUTH_FAILED**
   - Other errors → **CONNECTION_ERROR**
   - Error message is stored in `status_message`

### During Bot Operation

If a bot encounters an error while running:
- Exception is caught and logged
- Status is updated based on error type
- `last_status_check_at` timestamp is updated

### On Bot Stop

When a bot is manually stopped:
- Status is set to **DISCONNECTED**
- `status_message` is set to "Bot stopped manually"

## UI Display

### Admin RaceTime Bots View

The status is displayed in the bots table with:

1. **Active/Inactive Badge**: Shows if bot is enabled
2. **Connection Status Badge**: 
   - Color-coded by status (green=connected, red=errors, yellow=disconnected)
   - Includes status icon
   - Shows status name
   - Tooltip displays error message (if applicable)
3. **Last Connected Timestamp**: 
   - Displays when bot last successfully connected
   - Formatted in local timezone

### Example Display

```
┌──────────────┬──────────────────────────────────────────────────┐
│ Category     │ Status                                           │
├──────────────┼──────────────────────────────────────────────────┤
│ alttpr       │ ✓ Active                                         │
│              │ ✓ Connected                                      │
│              │ Last: 2025-01-03 14:30:25                        │
├──────────────┼──────────────────────────────────────────────────┤
│ sm           │ ✓ Active                                         │
│              │ ✗ Auth Failed                                    │
│              │ (hover for error: "Invalid client secret")       │
│              │ Last: 2025-01-03 12:15:00                        │
└──────────────┴──────────────────────────────────────────────────┘
```

## API Schema Updates

The `RacetimeBotOut` schema now includes status fields:

```python
class RacetimeBotOut(BaseModel):
    # ... existing fields ...
    status: int  # Status enum value
    status_message: Optional[str]  # Error details
    last_connected_at: Optional[datetime]  # Last successful connection
    last_status_check_at: Optional[datetime]  # Last status check
```

## Migration

Status tracking was added via Aerich migration:

```bash
poetry run aerich migrate --name "add_bot_status_tracking"
poetry run aerich upgrade
```

**Migration**: `26_20251103195308_add_bot_status_tracking.py`

This migration adds:
- `status` column (INT, default 0)
- `status_message` column (TEXT, nullable)
- `last_connected_at` column (DATETIME, nullable)
- `last_status_check_at` column (DATETIME, nullable)

## Usage Examples

### Check Bot Health

```python
from application.repositories.racetime_bot_repository import RacetimeBotRepository

repository = RacetimeBotRepository()

# Get all unhealthy bots
unhealthy_bots = await repository.get_unhealthy_bots()
for bot in unhealthy_bots:
    print(f"{bot.category}: {bot.get_status_display()}")
    if bot.status_message:
        print(f"  Error: {bot.status_message}")
```

### Monitor Bot Status

```python
# Get bot and check if healthy
bot = await repository.get_bot_by_id(bot_id)
if bot.is_healthy():
    print("Bot is operational")
else:
    print(f"Bot issue: {bot.get_status_display()}")
    print(f"Details: {bot.status_message}")
```

### Update Status Manually

```python
# Record connection success
await repository.record_connection_success(bot_id)

# Record authentication failure
await repository.record_connection_failure(
    bot_id,
    "OAuth2 token validation failed: Invalid client_secret",
    BotStatus.AUTH_FAILED
)
```

## Troubleshooting

### Bot Shows AUTH_FAILED

**Cause**: Invalid OAuth2 credentials

**Solution**:
1. Navigate to Admin > RaceTime Bots
2. Click edit on the affected bot
3. Verify `client_id` and `client_secret` against RaceTime.gg OAuth application
4. Update credentials and save
5. Restart the application to reconnect

### Bot Shows CONNECTION_ERROR

**Cause**: Network issues or RaceTime.gg service unavailable

**Solution**:
1. Check application logs for detailed error message
2. Verify network connectivity to racetime.gg
3. Check RaceTime.gg service status
4. Review `status_message` field for specific error details

### Bot Shows DISCONNECTED

**Cause**: Bot was manually stopped

**Solution**:
1. If bot should be running, set `is_active` to true
2. Restart the application to reconnect

### Bot Shows UNKNOWN

**Cause**: Bot has never attempted to connect

**Solution**:
1. Check that `is_active` is set to true
2. Restart the application to initiate connection
3. If status remains UNKNOWN after restart, check application logs

## Future Enhancements

Potential improvements to status tracking:

1. **Health Check Endpoint**: API endpoint to query bot health status
2. **Status Notifications**: Alert admins when bots go unhealthy
3. **Historical Status Log**: Track status changes over time
4. **Automatic Retry**: Attempt reconnection on transient failures
5. **Status Dashboard**: Dedicated page showing real-time bot health across all categories
6. **Prometheus Metrics**: Export bot status metrics for monitoring systems

## Related Files

- **Model**: `models/racetime_bot.py`
- **Repository**: `application/repositories/racetime_bot_repository.py`
- **Client**: `racetime/client.py`
- **Service**: `application/services/racetime_service.py`
- **View**: `views/admin/admin_racetime_bots.py`
- **API Schema**: `api/schemas/racetime_bot.py`
- **Migration**: `migrations/models/26_20251103195308_add_bot_status_tracking.py`
