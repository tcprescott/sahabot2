# RaceTime.gg Race Events

## Overview

The SahaBot2 racetime integration emits comprehensive events for all race-related activities. These events allow you to react to changes in real-time without polling the RaceTime.gg API.

## Available Events

### Race Status Changes

**`RacetimeRaceStatusChangedEvent`** - Emitted when a race changes status

**Fields:**
- `category` (str): Race category (e.g., "alttpr")
- `room_slug` (str): Full race room identifier (e.g., "alttpr/cool-doge-1234")
- `room_name` (str): Short room name (e.g., "cool-doge-1234")
- `old_status` (str): Previous status
- `new_status` (str): Current status
- `match_id` (Optional[int]): Associated match ID if any
- `tournament_id` (Optional[int]): Associated tournament ID if any
- `entrant_count` (int): Number of entrants in race
- `started_at` (Optional[str]): ISO 8601 datetime when race started
- `ended_at` (Optional[str]): ISO 8601 datetime when race ended

**Race Status Values:**
- `open`: Race room is open for entrants to join
- `invitational`: Race room is invite-only
- `pending`: Race countdown has started
- `in_progress`: Race is currently running
- `finished`: Race has completed
- `cancelled`: Race was cancelled

**Example:**
```python
from application.events import EventBus, RacetimeRaceStatusChangedEvent

@EventBus.on(RacetimeRaceStatusChangedEvent)
async def track_race_status(event: RacetimeRaceStatusChangedEvent):
    if event.new_status == 'in_progress':
        print(f"🏁 Race {event.room_name} has started with {event.entrant_count} entrants!")
    elif event.new_status == 'finished':
        print(f"✅ Race {event.room_name} completed at {event.ended_at}")
```

### Entrant Status Changes

**`RacetimeEntrantStatusChangedEvent`** - Emitted when a racer's status changes

**Fields:**
- `category` (str): Race category
- `room_slug` (str): Full race room identifier
- `room_name` (str): Short room name
- `racetime_user_id` (str): Racetime.gg user hash ID
- `racetime_user_name` (str): Racetime.gg user name
- `user_id` (Optional[int]): Application user ID if racetime account is linked, None otherwise
- `old_status` (Optional[str]): Previous status value
- `new_status` (str): Current status value
- `finish_time` (Optional[str]): ISO 8601 duration if finished (e.g., "PT1H23M45S")
- `place` (Optional[int]): Placement if finished (1, 2, 3, etc.)
- `match_id` (Optional[int]): Associated match ID if any
- `tournament_id` (Optional[int]): Associated tournament ID if any
- `race_status` (str): Current overall race status

**Entrant Status Values:**
- `requested`: User has requested to join (invitational races only)
- `invited`: User has been invited but not yet joined
- `not_ready`: User has joined but not marked ready
- `ready`: User is ready to race
- `in_progress`: User is currently racing
- `done`: User has finished the race
- `dnf`: User did not finish (forfeited)
- `dq`: User was disqualified

**User ID Resolution:**
The `user_id` field is automatically resolved by looking up the application User by their linked `racetime_id`. This enables authorization checks in service layer methods when handling racetime-triggered actions. If the racetime account is not linked to any application user, `user_id` will be None.

**Example:**
```python
from application.events import EventBus, RacetimeEntrantStatusChangedEvent

@EventBus.on(RacetimeEntrantStatusChangedEvent)
async def track_race_finishes(event: RacetimeEntrantStatusChangedEvent):
    if event.new_status == 'done':
        print(f"🏁 {event.racetime_user_name} finished in {event.place} place!")
        print(f"   Time: {event.finish_time}")
        
        # Use user_id for authorization checks
        if event.user_id:
            # User has linked racetime account - can update tournament data
            await tournament_service.record_finish(event.user_id, event.match_id, event.finish_time)
        else:
            # Unlinked racetime account - log but don't update
            print(f"   (Racetime account not linked - no tournament update)")
```

### Entrant Join/Leave Events

**`RacetimeEntrantJoinedEvent`** - Emitted when a player joins a race room

**Fields:**
- `category` (str): Race category
- `room_slug` (str): Full race room identifier
- `room_name` (str): Short room name
- `racetime_user_id` (str): Racetime.gg user hash ID
- `racetime_user_name` (str): Racetime.gg user name
- `user_id` (Optional[int]): Application user ID if racetime account is linked, None otherwise
- `initial_status` (str): Initial status when joining (usually "not_ready" or "requested")
- `match_id` (Optional[int]): Associated match ID if any
- `tournament_id` (Optional[int]): Associated tournament ID if any
- `race_status` (str): Current overall race status

**Example:**
```python
from application.events import EventBus, RacetimeEntrantJoinedEvent

@EventBus.on(RacetimeEntrantJoinedEvent)
async def welcome_new_racer(event: RacetimeEntrantJoinedEvent):
    print(f"👋 {event.racetime_user_name} joined {event.room_name}!")
    if event.initial_status == 'requested':
        print("   (Awaiting approval)")
    
    # Check if user has linked account for authorization
    if event.user_id:
        # Can grant tournament-specific permissions
        await tournament_service.auto_approve_participant(event.user_id, event.match_id)
```

**`RacetimeEntrantLeftEvent`** - Emitted when a player leaves a race room

**Fields:**
- `category` (str): Race category
- `room_slug` (str): Full race room identifier
- `room_name` (str): Short room name
- `racetime_user_id` (str): Racetime.gg user hash ID
- `racetime_user_name` (str): Racetime.gg user name
- `user_id` (Optional[int]): Application user ID if racetime account is linked, None otherwise
- `last_status` (str): Status when they left
- `match_id` (Optional[int]): Associated match ID if any
- `tournament_id` (Optional[int]): Associated tournament ID if any
- `race_status` (str): Current overall race status

**Example:**
```python
from application.events import EventBus, RacetimeEntrantLeftEvent

@EventBus.on(RacetimeEntrantLeftEvent)
async def track_dropouts(event: RacetimeEntrantLeftEvent):
    print(f"👋 {event.racetime_user_name} left {event.room_name}")
    if event.last_status == 'ready':
        print("   (They were ready to race)")
    
    # Handle tournament forfeit if user has linked account
    if event.user_id and event.match_id:
        await tournament_service.record_forfeit(event.user_id, event.match_id)
```

### Bot Invitation Events

**`RacetimeEntrantInvitedEvent`** - Emitted when the bot invites a player

**Fields:**
- `category` (str): Race category
- `room_slug` (str): Full race room identifier
- `room_name` (str): Short room name
- `racetime_user_id` (str): Racetime.gg user hash ID being invited
- `racetime_user_name` (Optional[str]): Racetime.gg user name (if available)
- `user_id` (Optional[int]): Application user ID if racetime account is linked, None otherwise
- `match_id` (Optional[int]): Associated match ID if any
- `tournament_id` (Optional[int]): Associated tournament ID if any
- `race_status` (str): Current overall race status

**Note:** This event only fires for invitations sent by this bot instance, not for invitations sent via the web UI or by other bots.

**Example:**
```python
from application.events import EventBus, RacetimeEntrantInvitedEvent

@EventBus.on(RacetimeEntrantInvitedEvent)
async def log_invitations(event: RacetimeEntrantInvitedEvent):
    print(f"📨 Invited {event.racetime_user_id} to {event.room_name}")
    
    # Send Discord notification if user has linked account
    if event.user_id:
        await discord_service.notify_race_invite(event.user_id, event.room_slug)
```

### Bot Room Management Events

**`RacetimeBotJoinedRaceEvent`** - Emitted when the bot joins an existing race

**Fields:**
- `category` (str): Race category
- `room_slug` (str): Full race room identifier
- `room_name` (str): Short room name
- `race_status` (str): Current race status when bot joined
- `entrant_count` (int): Number of entrants when bot joined
- `match_id` (Optional[int]): Associated match ID if any
- `tournament_id` (Optional[int]): Associated tournament ID if any
- `bot_action` (str): Always "join" for this event

**Example:**
```python
from application.events import EventBus, RacetimeBotJoinedRaceEvent

@EventBus.on(RacetimeBotJoinedRaceEvent)
async def bot_joined_race(event: RacetimeBotJoinedRaceEvent):
    print(f"🤖 Bot joined {event.room_name} ({event.entrant_count} entrants)")
```

**`RacetimeBotCreatedRaceEvent`** - Emitted when the bot creates/opens a new race room

**Fields:**
- `category` (str): Race category
- `room_slug` (str): Full race room identifier
- `room_name` (str): Short room name
- `goal` (str): Race goal text
- `invitational` (bool): Whether race is invite-only
- `match_id` (Optional[int]): Associated match ID if any
- `tournament_id` (Optional[int]): Associated tournament ID if any
- `bot_action` (str): Always "create" for this event

**Example:**
```python
from application.events import EventBus, RacetimeBotCreatedRaceEvent

@EventBus.on(RacetimeBotCreatedRaceEvent)
async def bot_created_race(event: RacetimeBotCreatedRaceEvent):
    print(f"🎮 Bot created race room: {event.room_name}")
    print(f"   Goal: {event.goal}")
    print(f"   Invitational: {event.invitational}")
```

## Complete Integration Example

Here's a complete example showing how to use multiple RaceTime events together:

```python
from application.events import (
    EventBus,
    RacetimeRaceStatusChangedEvent,
    RacetimeEntrantStatusChangedEvent,
    RacetimeEntrantJoinedEvent,
    RacetimeEntrantLeftEvent,
    RacetimeBotCreatedRaceEvent,
)
import logging

logger = logging.getLogger(__name__)

# Track when race starts
@EventBus.on(RacetimeRaceStatusChangedEvent)
async def on_race_status_change(event: RacetimeRaceStatusChangedEvent):
    if event.new_status == 'in_progress':
        logger.info("Race %s started at %s", event.room_name, event.started_at)
    elif event.new_status == 'finished':
        logger.info("Race %s finished at %s", event.room_name, event.ended_at)

# Welcome new racers
@EventBus.on(RacetimeEntrantJoinedEvent)
async def on_racer_joined(event: RacetimeEntrantJoinedEvent):
    logger.info("%s joined %s", event.racetime_user_name, event.room_name)

# Track race completions
@EventBus.on(RacetimeEntrantStatusChangedEvent)
async def on_entrant_status_change(event: RacetimeEntrantStatusChangedEvent):
    if event.new_status == 'done':
        logger.info(
            "%s finished %s in place %d (time: %s)",
            event.racetime_user_name,
            event.room_name,
            event.place,
            event.finish_time
        )
    elif event.new_status == 'dnf':
        logger.info("%s forfeited from %s", event.racetime_user_name, event.room_name)

# Log when bot creates rooms
@EventBus.on(RacetimeBotCreatedRaceEvent)
async def on_bot_created_room(event: RacetimeBotCreatedRaceEvent):
    logger.info(
        "Bot created race room %s (goal: %s, invitational: %s)",
        event.room_name,
        event.goal,
        event.invitational
    )
```

## Event Priority

All RaceTime events are assigned priorities:
- **HIGH**: Race status changes, bot room creation/joining
- **NORMAL**: Entrant status changes, joins, leaves, invitations

This ensures race-level events are processed before entrant-level events when both occur simultaneously.

## Technical Notes

### User ID Resolution

All entrant-related events (`RacetimeEntrantStatusChangedEvent`, `RacetimeEntrantJoinedEvent`, `RacetimeEntrantLeftEvent`, `RacetimeEntrantInvitedEvent`) include both:
- `racetime_user_id` - The racetime.gg user hash ID (always present)
- `user_id` - The application User ID (present only if racetime account is linked)

The `user_id` field enables **service layer authorization** when handling racetime-triggered actions.

**Three User ID States:**

1. **Positive ID (e.g., 42)** - Authenticated user with linked racetime account
2. **SYSTEM_USER_ID (-1)** - System/automation action (bot actions, race status changes)
3. **None** - Unknown/unauthenticated user (racetime account not linked to application)

```python
from models import SYSTEM_USER_ID, is_system_user_id, is_authenticated_user_id

@EventBus.on(RacetimeEntrantStatusChangedEvent)
async def on_race_finish(event: RacetimeEntrantStatusChangedEvent):
    if event.new_status == 'done':
        if is_authenticated_user_id(event.user_id):
            # Real user with linked account - can authorize service actions
            await tournament_service.record_race_result(
                user_id=event.user_id,
                match_id=event.match_id,
                finish_time=event.finish_time,
            )
        elif event.user_id is None:
            # Unlinked racetime account - log but don't update
            logger.warning("Race finish by unlinked user %s", event.racetime_user_id)
        elif is_system_user_id(event.user_id):
            # System action (shouldn't happen for entrant status changes)
            logger.warning("Unexpected system action for entrant event")
```

**System vs. Unknown Users:**

The distinction is important for security and auditing:
- **SYSTEM_USER_ID** explicitly indicates automated actions (bot creating races, race status changes)
- **None** indicates we don't know who the user is (unlinked racetime account)

This prevents security issues where an unauthenticated request might be confused with a legitimate system action.

**Helper Functions:**

```python
from models import is_system_user_id, is_authenticated_user_id, get_user_id_description

# Check if user_id is a system action
if is_system_user_id(event.user_id):
    logger.info("System automation triggered event")

# Check if user_id is a real authenticated user
if is_authenticated_user_id(event.user_id):
    # Safe to use for authorization
    user = await user_repository.get_by_id(event.user_id)

# Get human-readable description for logging/auditing
description = get_user_id_description(event.user_id)
# Returns: "User 42", "System/Automation", or "Unknown/Unauthenticated"
logger.info("Action by: %s", description)
```

**Lookup Process:**
1. When an entrant event is emitted, the handler calls `UserRepository.get_by_racetime_id(racetime_user_id)`
2. If a User with matching `racetime_id` is found, `user_id` is set to that User's ID
3. If no matching User is found, `user_id` is set to `None`
4. For system events (bot actions, race status changes), `user_id` is set to `SYSTEM_USER_ID`
5. Any errors during lookup are logged but don't prevent event emission

**Use Cases:**
- **Bot Chat Commands**: When a user triggers a bot command in racetime chat, you can identify them via `user_id` to check permissions
- **Tournament Integration**: Automatically record race results for users who have linked their racetime accounts
- **Notifications**: Send Discord DMs to users about their race status (join/finish/forfeit)
- **Authorization**: Enforce organization-scoped permissions when processing racetime events
- **Auditing**: Distinguish between user actions, system automation, and unknown/unauthenticated actions

### Event Detection

- **Race Status Changes**: Detected by comparing `status.value` in consecutive `race.data` WebSocket messages
- **Entrant Status Changes**: Detected by comparing each entrant's status between updates
- **Joins/Leaves**: Detected by comparing the set of entrant IDs between updates
- **Invitations**: Emitted when `SahaRaceHandler.invite_user()` is called
- **Bot Actions**: Emitted in `SahaRaceHandler.begin()` based on creation flag

### First Data Update

The handler skips emitting join/leave events on the first `race.data` update to avoid false positives when the bot first connects to a race room. All existing entrants are recorded as baseline state.

### Event Emission

All events are emitted via `EventBus.emit()` and run asynchronously. Event handlers are fire-and-forget—they don't block race processing even if they encounter errors.

## See Also

- [RaceTime Status Events Implementation](RACETIME_STATUS_EVENTS_IMPLEMENTATION.md) - Technical implementation details
- [Event System Documentation](EVENT_SYSTEM.md) - Core event system architecture
- [RaceTime.gg API Documentation](https://github.com/racetimeGG/racetime-app/wiki/Category-bots) - Official API docs

## How It Works

### Event Detection

The `SahaRaceHandler` class (in `racetime/client.py`) overrides the `race_data()` method from the base `RaceHandler` class. This method is called whenever the bot receives a `race.data` message from RaceTime.gg via WebSocket.

**Detection Logic:**
1. **Race Status Changes**: Compares `old_race_data.status.value` with `new_race_data.status.value`
2. **Entrant Status Changes**: Maintains a `_previous_entrant_statuses` dict keyed by user ID, comparing previous status with current status for each entrant

### Event Emission

Events are emitted asynchronously via the `EventBus`:

```python
await EventBus.emit(RacetimeRaceStatusChangedEvent(
    user_id=None,  # System event
    entity_id=room_slug,
    category=category,
    room_slug=room_slug,
    room_name=room_name,
    old_status=old_status,
    new_status=new_status,
    entrant_count=len(new_race_data.get('entrants', [])),
    started_at=new_race_data.get('started_at'),
    ended_at=new_race_data.get('ended_at'),
))
```

## Usage Examples

### Listening for Race Starts

```python
from application.events import EventBus, RacetimeRaceStatusChangedEvent

async def on_race_start(event: RacetimeRaceStatusChangedEvent):
    """Handle race start events."""
    if event.new_status == 'in_progress':
        logger.info(
            "Race %s started with %d entrants at %s",
            event.room_name,
            event.entrant_count,
            event.started_at
        )
        # Send notifications, update database, etc.

EventBus.on(RacetimeRaceStatusChangedEvent, on_race_start)
```

### Tracking Entrant Finishes

```python
from application.events import EventBus, RacetimeEntrantStatusChangedEvent

async def on_entrant_finish(event: RacetimeEntrantStatusChangedEvent):
    """Handle entrant finish events."""
    if event.new_status == 'done':
        logger.info(
            "%s finished race %s in place %d with time %s",
            event.racetime_user_name,
            event.room_name,
            event.place,
            event.finish_time
        )
        # Record finish time, update leaderboards, etc.

EventBus.on(RacetimeEntrantStatusChangedEvent, on_entrant_finish)
```

### Multi-Event Handler (Async Tournament Example)

```python
from application.events import (
    EventBus,
    RacetimeRaceStatusChangedEvent,
    RacetimeEntrantStatusChangedEvent
)

class AsyncTournamentRaceHandler:
    """Handle race events for async tournaments."""
    
    def __init__(self):
        # Register event listeners
        EventBus.on(RacetimeRaceStatusChangedEvent, self.handle_race_status)
        EventBus.on(RacetimeEntrantStatusChangedEvent, self.handle_entrant_status)
    
    async def handle_race_status(self, event: RacetimeRaceStatusChangedEvent):
        """Process race status changes."""
        if event.new_status == 'in_progress':
            # Record start times for eligible entrants
            await self.record_race_start(event)
        elif event.new_status == 'finished':
            # Finalize race results
            await self.finalize_race_results(event)
    
    async def handle_entrant_status(self, event: RacetimeEntrantStatusChangedEvent):
        """Process entrant status changes."""
        if event.new_status == 'done':
            # Record finish time
            await self.record_finish(event)
        elif event.new_status == 'dnf':
            # Mark as forfeit
            await self.record_forfeit(event)
```

## Integration with Original SahasrahBot Patterns

The original SahasrahBot dispatched similar events using Discord.py's event system:

```python
# Original SahasrahBot (alttprbot_racetime/handlers/core.py)
discordbot.dispatch(f"racetime_{status}", self, data)
```

These dispatched events like:
- `on_racetime_open`
- `on_racetime_invitational`
- `on_racetime_in_progress`
- `on_racetime_finished`
- `on_racetime_cancelled`

**SahaBot2's Approach:**
- Uses the application-wide `EventBus` instead of Discord bot dispatch
- Provides more granular events (race status + entrant status separately)
- Includes richer event data (timestamps, entrant details, etc.)
- Works across both Discord bot and web UI contexts

## Debugging and Monitoring

### Viewing Event Logs

Events are logged at INFO level when emitted:

```
INFO:racetime.client:Race alttpr/cool-doge-1234 status changed: pending -> in_progress
INFO:racetime.client:Entrant player123 (abc123) status changed in race alttpr/cool-doge-1234: ready -> in_progress
```

### Testing Event Handlers

You can manually emit events for testing:

```python
from application.events import EventBus, RacetimeRaceStatusChangedEvent

# Emit a test event
await EventBus.emit(RacetimeRaceStatusChangedEvent(
    user_id=None,
    entity_id="alttpr/test-race-1234",
    category="alttpr",
    room_slug="alttpr/test-race-1234",
    room_name="test-race-1234",
    old_status="pending",
    new_status="in_progress",
    entrant_count=4,
))
```

## Implementation Details

### File Locations

- **Event Definitions**: `application/events/types.py`
- **Event Exports**: `application/events/__init__.py`
- **Event Detection**: `racetime/client.py` (SahaRaceHandler class)
- **Event Bus**: `application/events/bus.py`

### Event Priority

- **Race Status Changes**: `EventPriority.HIGH` (75)
- **Entrant Status Changes**: `EventPriority.NORMAL` (50)

### Performance Considerations

- Events are emitted asynchronously (`await EventBus.emit()`)
- Event handlers run in parallel and errors are isolated
- No performance impact on race room WebSocket processing
- Entrant status tracking uses a lightweight dict (O(1) lookups)

## References

- [RaceTime.gg Bot Documentation](https://github.com/racetimeGG/racetime-app/wiki/Category-bots)
- [Original SahasrahBot racetime integration](https://github.com/tcprescott/sahasrahbot/tree/main/alttprbot_racetime)
- [racetime-bot Python library](https://github.com/racetimeGG/racetime-bot)
- [SahaBot2 Event System Documentation](EVENT_SYSTEM.md)
