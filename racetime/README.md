# Racetime.gg Bot Integration

This directory contains the racetime.gg bot integration for SahaBot2.

## Overview

The racetime bot integrates with [racetime.gg](https://racetime.gg) to provide race monitoring and management functionality. It uses the official [racetime-bot](https://github.com/racetimeGG/racetime-bot) library.

**Multi-Bot Architecture**: Racetime.gg requires a separate bot instance for each game category. This implementation supports running multiple bot instances simultaneously, each with its own OAuth2 credentials and category assignment.

## Important: Automatic Polling Disabled

**SahaBot2 does NOT use automatic race room polling**. The bot client explicitly disables the `refresh_races()` polling mechanism from the upstream racetime-bot library.

### Why Polling is Disabled

- **Precise Control**: We want explicit control over when and how race rooms are joined
- **Scheduler Integration**: Race rooms should be created/joined via the task scheduler system
- **Multi-Tenant Model**: Random auto-joining conflicts with organization-scoped automation
- **Resource Efficiency**: No continuous polling overhead

### How Race Rooms Are Joined

Instead of automatic polling, race rooms are joined **explicitly** via:

1. **Task Scheduler System** - Create scheduled tasks to open race rooms at specific times
2. **Manual Commands** - Discord bot commands like `!startrace`
3. **API Calls** - Programmatic creation via `bot.startrace()` or `bot.join_race_room()`

**See**: [`../docs/integrations/RACETIME_POLLING_DISABLED.md`](../docs/integrations/RACETIME_POLLING_DISABLED.md) for complete details.

## Configuration

Required environment variable (add to `.env`):

```bash
# Format: category:client_id:secret,category:client_id:secret,...
RACETIME_BOTS=alttpr:client_id_1:secret_1,smz3:client_id_2:secret_2
```

**Configuration Format**:
- Each bot is defined as `category:client_id:secret`
- Multiple bots are separated by commas
- Each category requires its own OAuth2 application on racetime.gg

### Getting Credentials

1. Go to https://racetime.gg/account/dev
2. Create a new OAuth2 application **for each category** you want to support
3. Copy the Client ID and Client Secret
4. Set the redirect URI (if needed)
5. Add each category's credentials to `RACETIME_BOTS` in the format above

## Architecture

The racetime bot system uses a **multi-instance pattern** (one bot per category):

- **`client.py`** - Bot implementation extending `racetime_bot.Bot` and `RaceHandler`
- **Multiple Instances**: One `RacetimeBot` instance per category, stored in `_racetime_bots` dict
- Access via `get_racetime_bot_instance(category)` from services
- Access all bots via `get_all_racetime_bot_instances()` for cross-category operations

## Bot Structure

### RacetimeBot Class

The `RacetimeBot` class extends the base `Bot` class from racetime-bot. Each instance:

- **Category-Specific**: Handles races for one specific game category
- **OAuth2 Credentials**: Uses category-specific client_id and client_secret

### SahaRaceHandler Class

The `SahaRaceHandler` class extends `RaceHandler` and handles individual race rooms:

- **Lifecycle Methods**: `begin()` and `end()` for setup/cleanup
- **Race Data Updates**: `race_data()` called when race state changes
- **Commands**: Monitor commands that can be used in race chat (using `@monitor_cmd`)

### Key Methods

- `begin()` - Called when handler is created (initial setup)
- `end()` - Called when handler is torn down (cleanup)
- `race_data()` - Called whenever race data is updated

### Commands

Commands are defined in the `SahaRaceHandler` class using the `@monitor_cmd` decorator:

```python
@monitor_cmd
async def ex_mycommand(self, args, message):
    """Command description."""
    await self.send_message("Response message")
```

## Usage

All configured bots automatically connect to racetime.gg when the application starts. Each bot will:

1. Authenticate using OAuth2 credentials
2. Monitor races in its assigned category
3. Respond to events and commands in race rooms

### Programmatic Access

```python
from racetime.client import get_racetime_bot_instance, get_all_racetime_bot_instances

# Get bot for specific category
alttpr_bot = get_racetime_bot_instance("alttpr")

# Get all bot instances
all_bots = get_all_racetime_bot_instances()  # Returns dict[str, RacetimeBot]
```

## Development

To add new functionality:

1. **Add Commands**: Use `@monitor_cmd` decorator in `SahaRaceHandler` for new commands
2. **Handle Race Updates**: Implement logic in `race_data()` method
3. **Setup/Cleanup**: Use `begin()` and `end()` methods for race lifecycle
4. **Use Services**: Delegate business logic to service layer (never access ORM directly)
5. **Logging**: Use lazy % formatting for all logging statements

## Important Notes

- The bot runs as a singleton within the application
- Commands go in the `SahaRaceHandler` class, not `RacetimeBot`
- Each race gets its own handler instance
- All business logic should be in the service layer
- The bot is presentation layer only (like Discord bot)
- Uses the same architectural principles as the rest of the application

## Example: Adding a Command

```python
from racetime_bot import monitor_cmd

class SahaRaceHandler(RaceHandler):
    @monitor_cmd
    async def ex_seed(self, args, message):
        """
        Display the seed for the current race.
        
        Usage: !seed
        """
        # Get seed from service (not database directly)
        seed_service = SeedService()
        seed = await seed_service.get_race_seed(self.data.get('name'))
        
        await self.send_message(f"Seed: {seed}")
```

## Testing

Test the bot by:

1. Starting the application: `./start.sh dev`
2. Creating a test race on racetime.gg
3. Joining the race room
4. Using commands like `!test`

## References

- [racetime-bot Documentation](https://github.com/racetimeGG/racetime-bot)
- [racetime.gg API](https://github.com/racetimeGG/racetime-app/wiki/OAuth2-API)
- [racetime.gg Developer Portal](https://racetime.gg/account/dev)
