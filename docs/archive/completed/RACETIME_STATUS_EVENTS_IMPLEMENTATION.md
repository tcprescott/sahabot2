# RaceTime.gg Status Change Event System - Implementation Summary

## Overview

This document describes the implementation of automatic event emission for RaceTime.gg race and entrant status changes in SahaBot2.

## Changes Made

### 1. New Event Types (`application/events/types.py`)

#### RacetimeRaceStatusChangedEvent
Emitted when overall race status changes (open → pending → in_progress → finished/cancelled).

```python
@dataclass(frozen=True)
class RacetimeRaceStatusChangedEvent(EntityEvent):
    """Emitted when a RaceTime.gg race changes status."""
    category: str              # e.g., "alttpr"
    room_slug: str             # e.g., "alttpr/cool-doge-1234"
    room_name: str             # e.g., "cool-doge-1234"
    old_status: Optional[str]  # Previous status value
    new_status: str            # Current status value
    entrant_count: int         # Number of entrants in race
    started_at: Optional[str]  # ISO 8601 datetime when race started
    ended_at: Optional[str]    # ISO 8601 datetime when race ended
    match_id: Optional[int]    # Associated match ID if any
    tournament_id: Optional[int]  # Associated tournament ID if any
    priority: EventPriority = EventPriority.HIGH
```

#### RacetimeEntrantStatusChangedEvent
Emitted when individual entrant status changes (not_ready → ready → in_progress → done/dnf/dq).

```python
@dataclass(frozen=True)
class RacetimeEntrantStatusChangedEvent(EntityEvent):
    """Emitted when a user's status in a RaceTime.gg race changes."""
    category: str              # e.g., "alttpr"
    room_slug: str             # e.g., "alttpr/cool-doge-1234"
    room_name: str             # e.g., "cool-doge-1234"
    racetime_user_id: str      # Racetime.gg user hash ID
    racetime_user_name: str    # Racetime.gg user name
    old_status: Optional[str]  # Previous status value
    new_status: str            # Current status value
    finish_time: Optional[str] # ISO 8601 duration if done
    place: Optional[int]       # Placement if finished
    race_status: str           # Current overall race status
    match_id: Optional[int]    # Associated match ID if any
    tournament_id: Optional[int]  # Associated tournament ID if any
    priority: EventPriority = EventPriority.NORMAL
```

### 2. Event Detection Logic (`racetime/client.py`)

#### SahaRaceHandler Enhancements

**Added State Tracking:**
```python
def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)
    # Track previous entrant statuses to detect changes
    self._previous_entrant_statuses: dict[str, str] = {}
```

**Overridden race_data() Method:**
- Compares old race data with new race data
- Detects race status changes (e.g., "pending" → "in_progress")
- Detects entrant status changes (e.g., "ready" → "in_progress", "in_progress" → "done")
- Emits events via EventBus for each detected change
- Maintains state for next comparison

**Race Status Detection:**
```python
old_status = old_race_data.get('status', {}).get('value') if old_race_data else None
new_status = new_race_data.get('status', {}).get('value')

if old_status and new_status and old_status != new_status:
    await EventBus.emit(RacetimeRaceStatusChangedEvent(...))
```

**Entrant Status Detection:**
```python
for entrant in new_entrants:
    user_id = entrant.get('user', {}).get('id', '')
    entrant_status = entrant.get('status', {}).get('value', '')
    
    old_entrant_status = self._previous_entrant_statuses.get(user_id)
    
    if old_entrant_status and old_entrant_status != entrant_status:
        await EventBus.emit(RacetimeEntrantStatusChangedEvent(...))
```

### 3. Event Exports (`application/events/__init__.py`)

Added new events to imports and exports:
```python
from .types import (
    # ... existing imports ...
    RacetimeRaceStatusChangedEvent,
    RacetimeEntrantStatusChangedEvent,
)

__all__ = [
    # ... existing exports ...
    "RacetimeRaceStatusChangedEvent",
    "RacetimeEntrantStatusChangedEvent",
]
```

### 4. Documentation (`docs/RACETIME_RACE_EVENTS.md`)

Comprehensive documentation covering:
- Overview of event system
- Detailed event field descriptions
- Race and entrant status value definitions
- Event detection logic explanation
- Usage examples for common scenarios
- Integration patterns from original SahasrahBot
- Debugging and monitoring tips
- Implementation details and file locations

## How It Works

### Event Flow

1. **WebSocket Message Received**: RaceTime.gg sends `race.data` message via WebSocket
2. **Handler Invoked**: `SahaRaceHandler.race_data(data)` is called
3. **Status Comparison**: Handler compares old vs new race/entrant statuses
4. **Event Emission**: Events emitted via `EventBus` for detected changes
5. **Event Handling**: Registered listeners receive and process events asynchronously

### Status Values

**Race Statuses:**
- `open` - Room open for entrants
- `invitational` - Invite-only mode
- `pending` - Countdown started
- `in_progress` - Race running
- `finished` - Race completed
- `cancelled` - Race cancelled

**Entrant Statuses:**
- `requested` - Join requested (invitational only)
- `invited` - Invited but not joined
- `not_ready` - Joined but not ready
- `ready` - Ready to race
- `in_progress` - Currently racing
- `done` - Finished the race
- `dnf` - Did not finish
- `dq` - Disqualified

## Usage Example

```python
from application.events import EventBus, RacetimeRaceStatusChangedEvent, RacetimeEntrantStatusChangedEvent

# Listen for race starts
async def on_race_start(event: RacetimeRaceStatusChangedEvent):
    if event.new_status == 'in_progress':
        logger.info("Race %s started with %d entrants", event.room_name, event.entrant_count)

EventBus.on(RacetimeRaceStatusChangedEvent, on_race_start)

# Listen for entrant finishes
async def on_finish(event: RacetimeEntrantStatusChangedEvent):
    if event.new_status == 'done':
        logger.info("%s finished in place %d", event.racetime_user_name, event.place)

EventBus.on(RacetimeEntrantStatusChangedEvent, on_finish)
```

## Integration with Existing Features

### Async Tournament Integration

These events can be used to automatically:
- Record start times when race status → `in_progress`
- Update race records when entrant status → `done`/`dnf`
- Mark forfeits when entrant status → `dnf`
- Finalize results when race status → `finished`

### Notification System Integration

Events can trigger Discord notifications:
- Race starting/finishing announcements
- Entrant finish time notifications
- Forfeit/DQ alerts for admins

### Audit Logging

All status changes are logged automatically:
- Race lifecycle tracking
- Entrant progression tracking
- Historical race data analysis

## Comparison with Original SahasrahBot

### Original Approach (Discord.py Events)
```python
# Original SahasrahBot
discordbot.dispatch(f"racetime_{status}", self, data)

# Listeners
@commands.Cog.listener()
async def on_racetime_in_progress(self, handler, data):
    # Handle race start
    pass
```

### SahaBot2 Approach (Event Bus)
```python
# SahaBot2
await EventBus.emit(RacetimeRaceStatusChangedEvent(...))

# Listeners
EventBus.on(RacetimeRaceStatusChangedEvent, on_race_start)
```

**Advantages:**
- ✅ Works across both Discord bot and web UI contexts
- ✅ Richer event data (timestamps, placement, etc.)
- ✅ Granular events (race status + entrant status separately)
- ✅ Type-safe event handling with dataclasses
- ✅ Built-in async error isolation
- ✅ Framework-agnostic (not tied to Discord.py)

## Testing

Events can be manually emitted for testing:

```python
from application.events import EventBus, RacetimeRaceStatusChangedEvent
from models import SYSTEM_USER_ID

# Emit test event
await EventBus.emit(RacetimeRaceStatusChangedEvent(
    user_id=SYSTEM_USER_ID,
    entity_id="alttpr/test-race-1234",
    category="alttpr",
    room_slug="alttpr/test-race-1234",
    room_name="test-race-1234",
    old_status="pending",
    new_status="in_progress",
    entrant_count=4,
))
```

## Performance Considerations

- **Event Emission**: Asynchronous, non-blocking
- **Event Handlers**: Run in parallel, errors isolated
- **State Tracking**: Lightweight dict with O(1) lookups
- **No Impact**: No performance impact on WebSocket processing
- **Scalability**: Handles multiple races/entrants efficiently

## Files Modified

1. **application/events/types.py**
   - Added `RacetimeRaceStatusChangedEvent`
   - Added `RacetimeEntrantStatusChangedEvent`

2. **application/events/__init__.py**
   - Exported new event types

3. **racetime/client.py**
   - Imported `EventBus` and event types
   - Enhanced `SahaRaceHandler.__init__()` with state tracking
   - Overrode `race_data()` to detect and emit status change events

4. **docs/RACETIME_RACE_EVENTS.md**
   - Created comprehensive documentation

## Future Enhancements

Potential future additions:
- **Match Association**: Automatically link events to Match/Tournament entities
- **Database Recording**: Persist status changes for historical analysis
- **Custom Filters**: Event filtering by category, tournament, etc.
- **Webhook Integration**: External webhook notifications for status changes
- **Analytics Dashboard**: Real-time race/entrant status visualization

## References

- [RaceTime.gg Category Bots Documentation](https://github.com/racetimeGG/racetime-app/wiki/Category-bots)
- [Original SahasrahBot racetime handlers](https://github.com/tcprescott/sahasrahbot/tree/main/alttprbot_racetime)
- [racetime-bot Python library](https://github.com/racetimeGG/racetime-bot)
- [SahaBot2 Event System](docs/EVENT_SYSTEM.md)
