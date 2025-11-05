# RaceTime Chat Commands - Implementation Summary

## Overview

Implemented a fully data-driven chat command system for racetime.gg rooms. Commands are prefixed with `!` and can be defined at the bot level (global) or tournament level (scoped).

## Key Design Decisions

### 1. Data-Driven Approach
**Unlike the original SahasrahBot** which hardcoded commands using the `@monitor_cmd` decorator, this implementation stores commands in the database. This allows:
- Tournament organizers to create custom commands without code deployment
- Different command sets per tournament
- Easy management via UI (future enhancement)
- Cooldowns, permissions, and scoping built-in

### 2. Hybrid Command System
Supports two response types:
- **TEXT**: Simple static responses (e.g., !rules, !discord)
- **DYNAMIC**: Python handlers for complex logic (e.g., !status, !entrants)

This balances simplicity (TEXT commands can be added without code) with power (DYNAMIC handlers for complex queries).

### 3. Scoped Commands
Three scope levels with priority:
1. **ASYNC_TOURNAMENT** (highest) - Async tournament rooms only
2. **TOURNAMENT** - Tournament match rooms only
3. **BOT** (lowest) - All rooms for a bot

This allows tournament-specific commands to override bot-wide defaults.

### 4. Built-in Handler Registry
Dynamic handlers are registered in a global service instance (`_get_command_service()`). This ensures:
- Handlers are registered once on first use
- All race handlers share the same command service
- No need to register per-handler

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Racetime.gg Room                         │
│                  (User types: !command args)                 │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                  SahaRaceHandler.chat_message()              │
│  - Parse command and arguments                               │
│  - Look up user (if racetime account linked)                │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│          RacetimeChatCommandService.execute_command()        │
│  - Find matching command (priority: async_tournament >      │
│    tournament > bot)                                         │
│  - Check linked account requirement                          │
│  - Check cooldown                                            │
│  - Execute command (TEXT or DYNAMIC)                         │
└───────────────────────────┬─────────────────────────────────┘
                            │
                   ┌────────┴────────┐
                   │                 │
        ┌──────────▼─────┐  ┌───────▼────────────┐
        │  TEXT Response │  │  DYNAMIC Response   │
        │  (from DB)     │  │  (call handler)     │
        └──────────┬─────┘  └───────┬────────────┘
                   │                 │
                   └────────┬────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│              Send response to racetime.gg room              │
└─────────────────────────────────────────────────────────────┘
```

## Files Created/Modified

### New Files

1. **models/racetime_chat_command.py**
   - `RacetimeChatCommand` model
   - `CommandScope` enum (BOT, TOURNAMENT, ASYNC_TOURNAMENT)
   - `CommandResponseType` enum (TEXT, DYNAMIC)

2. **application/repositories/racetime_chat_command_repository.py**
   - CRUD operations for commands
   - Query by scope (bot, tournament, async tournament)

3. **application/services/racetime_chat_command_service.py**
   - Command execution logic
   - Cooldown tracking
   - Handler registration and dispatch
   - Authorization checks

4. **racetime/command_handlers.py**
   - Built-in handlers:
     - `handle_help`: Display available commands
     - `handle_status`: Show race status and entrant count
     - `handle_race_info`: Display race goal/info
     - `handle_time`: Show user's finish time
     - `handle_entrants`: List entrants by status
   - `BUILTIN_HANDLERS` registry

5. **tools/add_example_racetime_commands.py**
   - Utility script to add example commands to database

6. **docs/RACETIME_CHAT_COMMANDS.md**
   - Comprehensive documentation
   - Usage examples
   - Handler development guide
   - Migration guide from original SahasrahBot

7. **migrations/models/34_20251104140153_add_racetime_chat_commands.py**
   - Database migration for `racetime_chat_commands` table

### Modified Files

1. **models/__init__.py**
   - Exported new models and enums

2. **racetime/client.py**
   - Added `_get_command_service()` for singleton command service
   - Added `chat_message()` handler to `SahaRaceHandler`
   - Modified `__init__()` to initialize command service and context
   - Modified `begin()` to capture bot_id for command lookups

## Database Schema

```sql
CREATE TABLE `racetime_chat_commands` (
    `id` INT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    `command` VARCHAR(50) NOT NULL COMMENT 'Command name without prefix',
    `description` LONGTEXT COMMENT 'Command description',
    `response_type` SMALLINT NOT NULL DEFAULT 0,
    `response_text` LONGTEXT,
    `handler_name` VARCHAR(100),
    `scope` SMALLINT NOT NULL,
    `require_linked_account` BOOL NOT NULL DEFAULT 0,
    `cooldown_seconds` INT NOT NULL DEFAULT 0,
    `is_active` BOOL NOT NULL DEFAULT 1,
    `created_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    `updated_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
    `async_tournament_id` INT,
    `racetime_bot_id` INT,
    `tournament_id` INT,
    UNIQUE KEY (`racetime_bot_id`, `command`),
    UNIQUE KEY (`tournament_id`, `command`),
    UNIQUE KEY (`async_tournament_id`, `command`),
    FOREIGN KEY (`async_tournament_id`) REFERENCES `async_tournaments` (`id`) ON DELETE CASCADE,
    FOREIGN KEY (`racetime_bot_id`) REFERENCES `racetime_bots` (`id`) ON DELETE CASCADE,
    FOREIGN KEY (`tournament_id`) REFERENCES `tournament` (`id`) ON DELETE CASCADE
) CHARACTER SET utf8mb4;
```

## Usage

### Adding Bot-Wide Commands

```python
from models import RacetimeChatCommand, CommandScope, CommandResponseType

# Simple text response
await RacetimeChatCommand.create(
    command='discord',
    description='Link to Discord server',
    scope=CommandScope.BOT,
    response_type=CommandResponseType.TEXT,
    response_text='Join us on Discord: https://discord.gg/example',
    racetime_bot_id=bot.id,
    is_active=True,
)

# Dynamic handler
await RacetimeChatCommand.create(
    command='status',
    description='Show race status',
    scope=CommandScope.BOT,
    response_type=CommandResponseType.DYNAMIC,
    handler_name='handle_status',
    racetime_bot_id=bot.id,
    is_active=True,
)
```

### Adding Tournament Commands

```python
# Override bot-wide !rules for this tournament
await RacetimeChatCommand.create(
    command='rules',
    description='Tournament-specific rules',
    scope=CommandScope.TOURNAMENT,
    response_type=CommandResponseType.TEXT,
    response_text='Special rules for Tournament #5',
    tournament_id=5,
    is_active=True,
)
```

### Using Commands

In any racetime.gg room where the bot is present:

```
Player: !status
Bot: Race Status: In Progress | Entrants: 4 (3 ready)

Player: !race
Bot: Goal: Beat the game | Info: Casual race, no streaming required

Player: !entrants
Bot: Ready: Alice, Bob | Not Ready: Charlie | Done: Dave
```

## Testing

Run the example commands script:

```bash
poetry run python tools/add_example_racetime_commands.py
```

This will create 5 example commands for the ALTTPR bot:
- `!help` - Display available commands
- `!status` - Show race status
- `!race` - Show race goal/info
- `!rules` - Tournament rules (with 30s cooldown)
- `!entrants` - List entrants

## Future Enhancements

- [ ] UI for command management in admin panel
- [ ] API endpoints for CRUD operations
- [ ] Command aliases (multiple names for same command)
- [ ] Conditional commands (only show if race status = X)
- [ ] Usage statistics/analytics
- [ ] Import/export command sets
- [ ] Tournament command templates
- [ ] Per-user command permissions

## Comparison to Original SahasrahBot

### Original (Hardcoded)

```python
@monitor_cmd
async def ex_help(self, args, message):
    await self.send_message("Help text")
```

- Commands hardcoded in bot code
- No per-tournament customization
- Changes require code deployment
- No cooldowns or permissions

### New (Data-Driven)

```python
# Database entry
RacetimeChatCommand.create(
    command='help',
    handler_name='handle_help',
    ...
)

# Handler in code
async def handle_help(command, args, racetime_user_id, race_data, user):
    return "Help text"
```

- Commands in database
- Per-tournament customization
- Changes without deployment
- Built-in cooldowns and permissions
- Linked account requirements
- Scope-based priority

## Benefits

1. **Flexibility**: Tournament organizers can create custom commands
2. **Maintainability**: Commands separated from handler logic
3. **Scalability**: Easy to add new commands without code changes
4. **Security**: Authorization built-in, linked account requirements
5. **UX**: Cooldowns prevent spam, scoping enables customization
6. **Compatibility**: Both static (TEXT) and dynamic (DYNAMIC) commands supported

## Migration Path

For organizations moving from the original SahasrahBot:

1. **Identify existing commands** in the old codebase
2. **Create database entries** for each command
3. **Implement handlers** for dynamic commands
4. **Test in dev environment** before production rollout
5. **Document custom commands** for tournament organizers

See `docs/RACETIME_CHAT_COMMANDS.md` for detailed migration guide.
