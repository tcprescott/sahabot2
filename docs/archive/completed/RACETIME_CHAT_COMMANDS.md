# RaceTime Chat Commands

## Overview

SahaBot2 now supports data-driven chat commands in racetime.gg rooms, prefixed with `!`. Unlike the original SahasrahBot which used hardcoded commands, this system allows commands to be defined either:

1. **Statically in code** - Built-in handlers for common functionality
2. **Dynamically in the database** - Per-bot or per-tournament custom commands

This provides maximum flexibility - administrators can create custom commands without code changes, while developers can add reusable handlers that reference database-configured commands.

## Architecture

### Components

1. **Model** (`models/racetime_chat_command.py`):
   - `RacetimeChatCommand`: Stores command definitions
   - `CommandScope`: BOT | TOURNAMENT | ASYNC_TOURNAMENT
   - `CommandResponseType`: TEXT | DYNAMIC

2. **Repository** (`application/repositories/racetime_chat_command_repository.py`):
   - CRUD operations for commands
   - Queries by scope (bot, tournament, async tournament)

3. **Service** (`application/services/racetime_chat_command_service.py`):
   - Business logic and authorization
   - Command execution and cooldown tracking
   - Handler registration and dispatch

4. **Handler Integration** (`racetime/client.py`):
   - `SahaRaceHandler.chat_message()`: Intercepts chat messages
   - Parses `!command` syntax and executes commands

5. **Built-in Handlers** (`racetime/command_handlers.py`):
   - Pre-built handlers for common commands
   - Registered automatically on bot startup

## Command Scopes

Commands can be scoped to different levels:

### BOT Scope
Available in all rooms handled by a specific racetime bot.

**Use cases:**
- General help commands
- Bot status/version info
- Universal tournament rules

**Example:**
```python
RacetimeChatCommand.create(
    command='help',
    scope=CommandScope.BOT,
    racetime_bot_id=1,  # ALTTPR bot
    ...
)
```

### TOURNAMENT Scope
Available only in rooms for a specific tournament (Match model).

**Use cases:**
- Tournament-specific rules
- Bracket/standings info
- Tournament coordinator contact

**Example:**
```python
RacetimeChatCommand.create(
    command='bracket',
    scope=CommandScope.TOURNAMENT,
    tournament_id=5,
    ...
)
```

### ASYNC_TOURNAMENT Scope
Available only in async tournament rooms (AsyncTournament model).

**Use cases:**
- Pool/permalink info
- Scoring rules
- Leaderboard links

**Example:**
```python
RacetimeChatCommand.create(
    command='pools',
    scope=CommandScope.ASYNC_TOURNAMENT,
    async_tournament_id=3,
    ...
)
```

## Response Types

### TEXT Response
Simple static text response.

**Example:**
```python
RacetimeChatCommand.create(
    command='rules',
    response_type=CommandResponseType.TEXT,
    response_text=(
        "Tournament Rules: 1) Be respectful. "
        "2) Follow seed settings. "
        "3) Have fun! Full rules: https://example.com/rules"
    ),
    ...
)
```

**When triggered:**
```
Player: !rules
Bot: Tournament Rules: 1) Be respectful. 2) Follow seed settings. 3) Have fun! Full rules: https://example.com/rules
```

### DYNAMIC Response
Calls a registered Python handler function.

**Example:**
```python
RacetimeChatCommand.create(
    command='status',
    response_type=CommandResponseType.DYNAMIC,
    handler_name='handle_status',  # Must be registered
    ...
)
```

**When triggered:**
```
Player: !status
Bot: Race Status: In Progress | Entrants: 4 (3 ready)
```

## Creating Commands

### Via Database (Recommended for Custom Commands)

Use the utility script:

```bash
poetry run python tools/add_example_racetime_commands.py
```

Or programmatically:

```python
from models import RacetimeChatCommand, CommandScope, CommandResponseType

# Simple text command
await RacetimeChatCommand.create(
    command='discord',  # Without ! prefix
    description='Link to Discord server',
    scope=CommandScope.BOT,
    response_type=CommandResponseType.TEXT,
    response_text='Join us on Discord: https://discord.gg/example',
    racetime_bot_id=bot.id,
    cooldown_seconds=60,  # Optional: 60 second cooldown
    is_active=True,
)
```

### Via Code (Built-in Handlers)

1. **Create the handler** in `racetime/command_handlers.py`:

```python
async def handle_custom(
    command: RacetimeChatCommand,
    args: list[str],
    racetime_user_id: str,
    race_data: dict,
    user: Optional[User],
) -> str:
    """
    Custom command handler.
    
    Args:
        command: The command object from database
        args: Command arguments (split by spaces)
        racetime_user_id: Racetime user hash ID
        race_data: Current race data from racetime.gg
        user: Application user (if racetime account is linked)
        
    Returns:
        Response text to send to chat
    """
    # Your logic here
    return "Custom response based on race state"
```

2. **Register in BUILTIN_HANDLERS**:

```python
BUILTIN_HANDLERS = {
    ...
    'handle_custom': handle_custom,
}
```

3. **Create database entry** referencing the handler:

```python
await RacetimeChatCommand.create(
    command='custom',
    response_type=CommandResponseType.DYNAMIC,
    handler_name='handle_custom',  # Must match BUILTIN_HANDLERS key
    ...
)
```

## Built-in Handlers

The following handlers are included out-of-the-box:

### `handle_help`
Displays help information.
```
Player: !help
Bot: Available commands: !help, !status, !race. Use !command for details.
```

### `handle_status`
Shows current race status and entrant count.
```
Player: !status
Bot: Race Status: In Progress | Entrants: 4 (3 ready)
```

### `handle_race_info`
Displays race goal and info text.
```
Player: !race
Bot: Goal: Beat the game | Info: Casual race, no streaming required
```

### `handle_time`
Shows user's finish time or current race time.
```
Player: !time
Bot: Your finish time: 1:23:45.67
```

### `handle_entrants`
Lists all entrants grouped by status.
```
Player: !entrants
Bot: Ready: Alice, Bob | Not Ready: Charlie | Done: Dave
```

## Features

### Cooldowns

Prevent spam by adding cooldowns:

```python
RacetimeChatCommand.create(
    ...
    cooldown_seconds=30,  # 30 second cooldown per user
)
```

When a user tries to use the command before cooldown expires:
```
Player: !rules
Bot: Command on cooldown. Try again in 15 seconds.
```

### Require Linked Account

Some commands may require users to have their racetime account linked to the application:

```python
RacetimeChatCommand.create(
    ...
    require_linked_account=True,
)
```

If unlinked:
```
Player: !myprofile
Bot: This command requires a linked racetime account. Visit the website to link your account.
```

### Command Arguments

Handlers receive parsed arguments:

```python
async def handle_lookup(command, args, racetime_user_id, race_data, user):
    if not args:
        return "Usage: !lookup <username>"
    
    username = args[0]
    # Look up player stats...
    return f"Stats for {username}: ..."
```

Usage:
```
Player: !lookup Alice
Bot: Stats for Alice: 15 races, 3 wins, avg time 1:25:30
```

## Priority and Overrides

When multiple commands with the same name exist at different scopes, priority is:

1. **ASYNC_TOURNAMENT** (highest)
2. **TOURNAMENT**
3. **BOT** (lowest)

This allows tournament-specific commands to override bot-wide defaults.

Example:
```python
# Bot-wide !rules command
RacetimeChatCommand.create(
    command='rules',
    scope=CommandScope.BOT,
    response_text="General racing rules",
    racetime_bot_id=1,
)

# Tournament-specific override
RacetimeChatCommand.create(
    command='rules',
    scope=CommandScope.TOURNAMENT,
    response_text="Special tournament rules for this event",
    tournament_id=5,
)
```

In tournament 5's rooms, `!rules` will show the tournament-specific text.

## Use Cases

### Community Server Bot
```python
# Welcome message
await RacetimeChatCommand.create(
    command='welcome',
    response_text="Welcome to ALTTPR racing! Type !help for commands.",
    scope=CommandScope.BOT,
    racetime_bot_id=alttpr_bot.id,
)

# Discord link
await RacetimeChatCommand.create(
    command='discord',
    response_text="Join our Discord: https://discord.gg/alttpr",
    scope=CommandScope.BOT,
    racetime_bot_id=alttpr_bot.id,
    cooldown_seconds=300,  # 5 minute cooldown
)
```

### Tournament Commands
```python
# Bracket link
await RacetimeChatCommand.create(
    command='bracket',
    response_text="Tournament bracket: https://challonge.com/mytourney",
    scope=CommandScope.TOURNAMENT,
    tournament_id=tournament.id,
)

# Coordinator contact
await RacetimeChatCommand.create(
    command='admin',
    response_text="Need help? Contact @TourneyAdmin on Discord",
    scope=CommandScope.TOURNAMENT,
    tournament_id=tournament.id,
)
```

### Dynamic Commands
```python
# Leaderboard
await RacetimeChatCommand.create(
    command='top10',
    response_type=CommandResponseType.DYNAMIC,
    handler_name='handle_leaderboard',
    scope=CommandScope.ASYNC_TOURNAMENT,
    async_tournament_id=async_tournament.id,
)

# Handler would query database and return top 10 players
```

## Database Schema

```sql
CREATE TABLE racetime_chat_commands (
    id INT PRIMARY KEY AUTO_INCREMENT,
    command VARCHAR(50) NOT NULL,
    description TEXT,
    response_type ENUM('TEXT', 'DYNAMIC'),
    response_text TEXT,
    handler_name VARCHAR(100),
    scope ENUM('BOT', 'TOURNAMENT', 'ASYNC_TOURNAMENT'),
    racetime_bot_id INT,
    tournament_id INT,
    async_tournament_id INT,
    require_linked_account BOOLEAN DEFAULT FALSE,
    cooldown_seconds INT DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    UNIQUE KEY(racetime_bot_id, command),
    UNIQUE KEY(tournament_id, command),
    UNIQUE KEY(async_tournament_id, command),
    
    FOREIGN KEY(racetime_bot_id) REFERENCES racetime_bots(id),
    FOREIGN KEY(tournament_id) REFERENCES tournament(id),
    FOREIGN KEY(async_tournament_id) REFERENCES async_tournaments(id)
);
```

## API Endpoints

Future enhancement: Add REST API endpoints for command management:

```
GET    /api/racetime/commands                    # List all commands
GET    /api/racetime/bots/{bot_id}/commands      # List bot commands
GET    /api/racetime/tournaments/{id}/commands   # List tournament commands
POST   /api/racetime/commands                    # Create command
PATCH  /api/racetime/commands/{id}               # Update command
DELETE /api/racetime/commands/{id}               # Delete command
```

## Security Considerations

1. **Authorization**: Command CRUD requires ADMIN permission
2. **Input Validation**: Command names are sanitized (lowercase, alphanumeric)
3. **Rate Limiting**: Cooldowns prevent spam
4. **Handler Safety**: Dynamic handlers should catch exceptions gracefully
5. **Account Linking**: Sensitive commands can require linked accounts

## Testing

Test commands in a racetime room:

```
# Join a room
!test

# If the command exists and is active, the bot will respond
```

Check logs for debugging:
```bash
# View racetime bot logs
poetry run python -c "import logging; logging.basicConfig(level=logging.DEBUG)"
```

## Future Enhancements

- [ ] UI for command management (admin panel)
- [ ] Command aliases (multiple names for same command)
- [ ] Conditional commands (only show if race status = X)
- [ ] Command categories/help grouping
- [ ] Usage statistics (most used commands)
- [ ] Import/export command sets
- [ ] Command templates library
- [ ] Per-user permissions for commands
- [ ] Scheduled commands (auto-post at race start, etc.)
- [ ] Command chaining/macros

## Troubleshooting

### Command not responding

1. **Check if command exists**:
   ```python
   cmd = await RacetimeChatCommand.filter(command='mycommand', is_active=True).first()
   print(cmd)
   ```

2. **Check bot_id is set**: Handler needs to know which bot to query commands for
   ```python
   # In handler begin() method
   logger.info("Handler bot_id: %s", self._bot_id)
   ```

3. **Check handler is registered**:
   ```python
   # In racetime/client.py
   logger.info("Registered handlers: %s", _command_service._dynamic_handlers.keys())
   ```

4. **Check cooldown**: Command may be on cooldown

5. **Check scope matching**: Tournament/async tournament IDs must match

### Handler errors

- Check logs for exceptions in handler execution
- Ensure handler signature matches: `async def handler(command, args, racetime_user_id, race_data, user) -> str`
- Return strings, not other types
- Catch and handle exceptions gracefully

## Migration from Original SahasrahBot

The original SahasrahBot used `@monitor_cmd` decorator for chat commands. To migrate:

**Old (SahasrahBot):**
```python
@monitor_cmd
async def ex_help(self, args, message):
    await self.send_message("Help text here")
```

**New (SahaBot2):**

1. Create handler:
```python
async def handle_help(command, args, racetime_user_id, race_data, user):
    return "Help text here"
```

2. Register in BUILTIN_HANDLERS

3. Create database entry:
```python
await RacetimeChatCommand.create(
    command='help',
    handler_name='handle_help',
    ...
)
```

**Benefits:**
- Commands can be added/modified without code deployment
- Tournament organizers can customize commands
- Cooldowns and permissions built-in
- Centralized command management
