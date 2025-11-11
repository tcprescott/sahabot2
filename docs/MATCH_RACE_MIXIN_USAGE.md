# MatchRaceMixin Usage Guide

This guide explains how to use the MatchRaceMixin pattern for tournament match race handlers.

## Overview

The `MatchRaceMixin` allows tournament match races to use both:
- **Match-specific functionality**: Automatic race finish processing and result recording
- **Category-specific commands**: Game-specific commands like `!mystery`, `!vt`, `!varia`, etc.

## Architecture

### Before (Limited Functionality)

Previously, `MatchRaceHandler` extended `SahaRaceHandler` directly:

```
MatchRaceHandler → SahaRaceHandler → RaceHandler
```

This meant tournament matches could only use base commands, not category-specific commands.

### After (Full Functionality)

Now, `MatchRaceMixin` can be combined with any handler:

```
MatchALTTPRRaceHandler → MatchRaceMixin → ALTTPRRaceHandler → SahaRaceHandler → RaceHandler
```

This provides both match processing AND category-specific commands.

## Available Combined Handlers

The system automatically creates these combined handlers:

1. **MatchALTTPRRaceHandler**: Match processing + ALTTPR commands
   - `!mystery <preset>` - Generate mystery seed
   - `!vt <preset>` - Generate ALTTPR seed
   - `!vtspoiler <preset> [studytime]` - Generate seed with spoiler
   - `!avianart <preset>` - Generate Avianart door randomizer seed
   - `!custommystery` - Information about custom mystery

2. **MatchSMRaceHandler**: Match processing + Super Metroid commands
   - `!varia [preset]` - Generate VARIA seed
   - `!dash [preset]` - Generate DASH seed
   - `!total [preset]` - Generate total randomization seed
   - `!multiworld [preset] [players]` - Generate multiworld seed

3. **MatchSMZ3RaceHandler**: Match processing + SMZ3 commands
   - `!race [preset]` - Generate SMZ3 seed
   - `!preset <name>` - Generate seed using preset
   - `!spoiler [preset]` - Generate seed with spoiler log

4. **MatchSahaRaceHandler**: Match processing + base commands only
   - `!help` - Show available commands
   - `!status` - Show race status
   - `!race` - Show race goal and info
   - `!time` - Show your finish time
   - `!entrants` - List all entrants

All handlers also include match-specific functionality:
- Automatic race finish detection
- Automatic result recording for match players
- Integration with TournamentService

## How It Works

### 1. Handler Creation

When a tournament match race room is created, the system:

1. Determines the bot's configured handler class (e.g., `ALTTPRRaceHandler`)
2. Creates a match-specific variant using `create_match_handler_class()`
3. Instantiates the handler with both bot and match information

### 2. Method Resolution Order (MRO)

The Python MRO ensures correct method chaining:

```python
MatchALTTPRRaceHandler.__mro__ = [
    MatchALTTPRRaceHandler,  # Combined class
    MatchRaceMixin,          # Match processing (called first)
    ALTTPRRaceHandler,       # ALTTPR commands
    SahaRaceHandler,         # Base commands
    RaceHandler,             # racetime-bot base
    object
]
```

When `race_data()` is called:
1. `MatchRaceMixin.race_data()` runs first (checks for race finish)
2. Calls `super().race_data()` to delegate to parent handlers
3. Parent handlers process their own logic (events, status changes, etc.)

### 3. Automatic Result Recording

When a race finishes:

1. `MatchRaceMixin.race_data()` detects status change to "finished"
2. Extracts finish times and placements from race data
3. Calls `TournamentService.process_match_race_finish()` with results
4. Service records results in database and advances match status

## Usage in Code

### Creating a Match Handler (Automatic)

The `RacetimeBot.create_match_handler()` method handles this automatically:

```python
from racetime.client import get_racetime_bot_instance

# Get bot for category
bot = get_racetime_bot_instance("alttpr")

# Create match handler (combines bot's handler with MatchRaceMixin)
handler = bot.create_match_handler(race_data, match_id=123)

# The handler now has:
# - Match processing (from MatchRaceMixin)
# - ALTTPR commands (from ALTTPRRaceHandler)
# - All base commands (from SahaRaceHandler)
```

### Creating a Match Handler (Manual)

For testing or manual creation:

```python
from racetime.match_race_handler import create_match_handler_class
from racetime.alttpr_handler import ALTTPRRaceHandler

# Create combined class
MatchALTTPRRaceHandler = create_match_handler_class(ALTTPRRaceHandler)

# Instantiate with match_id
handler = MatchALTTPRRaceHandler(
    bot_instance=bot,
    match_id=123,
    # ... other handler kwargs
)
```

## Testing Combined Handlers

Tests verify that combined handlers have both match and category functionality:

```python
def test_match_handler_has_alttpr_commands():
    MatchALTTPRRaceHandler = create_match_handler_class(ALTTPRRaceHandler)
    
    # Verify ALTTPR commands available
    assert hasattr(MatchALTTPRRaceHandler, "ex_mystery")
    assert hasattr(MatchALTTPRRaceHandler, "ex_vt")
    
    # Verify match processing available
    assert hasattr(MatchALTTPRRaceHandler, "race_data")
```

See `tests/unit/test_match_race_mixin.py` for comprehensive tests.

## Benefits

1. **Code Reuse**: No need to duplicate command implementations
2. **Maintainability**: Changes to category handlers automatically apply to match variants
3. **Flexibility**: Easy to add new combined handlers for new categories
4. **Type Safety**: Proper inheritance chain ensures all methods are available

## Implementation Details

### MatchRaceMixin Class

```python
class MatchRaceMixin:
    """
    Mixin for tournament match races.
    
    Adds match processing to any race handler via multiple inheritance.
    Must be placed BEFORE the base handler in the inheritance list.
    """
    
    def __init__(self, *args, match_id: int, **kwargs):
        super().__init__(*args, **kwargs)
        self.match_id = match_id
        self._race_finished = False
    
    async def race_data(self, data):
        # Call parent to handle standard events
        await super().race_data(data)
        
        # Add match processing after parent completes
        # ...
```

### create_match_handler_class() Function

```python
def create_match_handler_class(base_handler_class):
    """
    Dynamically create a match handler class.
    
    Combines MatchRaceMixin with any base handler using multiple inheritance.
    MRO ensures mixin methods are called first, with proper super() delegation.
    """
    class CombinedMatchRaceHandler(MatchRaceMixin, base_handler_class):
        pass
    
    # Set descriptive name
    CombinedMatchRaceHandler.__name__ = f"Match{base_handler_class.__name__}"
    
    return CombinedMatchRaceHandler
```

## Migration Notes

**Breaking Changes**: None - this is a backward-compatible refactor.

**Old Code**: References to `MatchRaceHandler` class still work (though it's now generated dynamically).

**New Code**: Use `create_match_handler_class()` or `bot.create_match_handler()` for creating match handlers.

## Related Files

- `racetime/match_race_handler.py` - MatchRaceMixin implementation
- `racetime/client.py` - RacetimeBot with handler creation
- `application/services/racetime/racetime_room_service.py` - Match room creation
- `tests/unit/test_match_race_mixin.py` - Comprehensive tests

## Summary

The MatchRaceMixin pattern provides a clean, maintainable way to combine match-specific functionality with category-specific commands, enabling tournament matches to use the full range of available race room commands while maintaining automatic result processing.
