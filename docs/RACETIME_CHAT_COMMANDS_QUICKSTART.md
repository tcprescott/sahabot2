# RaceTime Chat Commands - Quick Start

## What is this?

A data-driven chat command system for racetime.gg rooms. Commands are prefixed with `!` and can be:

- **Defined in the database** (no code changes needed)
- **Scoped** to bots, tournaments, or async tournaments
- **Static text** or **dynamic** (call Python handlers)
- **Customized** per tournament

## Quick Setup

### 1. Apply Migration

The migration creates the `racetime_chat_commands` table:

```bash
poetry run aerich upgrade
```

### 2. Add Example Commands

```bash
poetry run python tools/add_example_racetime_commands.py
```

This creates 5 example commands for your ALTTPR bot:
- `!help` - Display available commands
- `!status` - Show race status
- `!race` - Show race goal/info
- `!rules` - Tournament rules (30s cooldown)
- `!entrants` - List entrants

### 3. Test in a Racetime Room

Join any racetime.gg room where your bot is present and type:

```
!status
```

The bot will respond with:
```
Race Status: Open | Entrants: 2 (1 ready)
```

## Creating Your Own Commands

### Simple Text Command

```python
from models import RacetimeChatCommand, CommandScope, CommandResponseType, RacetimeBot

bot = await RacetimeBot.filter(category='alttpr').first()

await RacetimeChatCommand.create(
    command='discord',  # Triggered by: !discord
    description='Link to Discord server',
    scope=CommandScope.BOT,  # Available in all rooms
    response_type=CommandResponseType.TEXT,
    response_text='Join us on Discord: https://discord.gg/yourserver',
    racetime_bot_id=bot.id,
    cooldown_seconds=60,  # Optional: 60s cooldown
    is_active=True,
)
```

### Dynamic Command

1. **Create the handler** in `racetime/command_handlers.py`:

```python
async def handle_leaderboard(command, args, racetime_user_id, race_data, user):
    """Show tournament leaderboard."""
    # Query database for top players
    # Format response
    return "Top 3: Alice (120 pts), Bob (115 pts), Charlie (100 pts)"
```

2. **Register in BUILTIN_HANDLERS**:

```python
BUILTIN_HANDLERS = {
    ...
    'handle_leaderboard': handle_leaderboard,
}
```

3. **Create database entry**:

```python
await RacetimeChatCommand.create(
    command='leaderboard',
    scope=CommandScope.TOURNAMENT,
    response_type=CommandResponseType.DYNAMIC,
    handler_name='handle_leaderboard',
    tournament_id=5,  # Only for tournament #5
    is_active=True,
)
```

## Command Scopes

Commands can be scoped to different levels (with priority):

1. **ASYNC_TOURNAMENT** (highest) - Async tournament rooms only
2. **TOURNAMENT** - Tournament match rooms only  
3. **BOT** (lowest) - All rooms for this bot

Higher-scoped commands override lower-scoped ones with the same name.

## Built-in Handlers

These handlers are ready to use out-of-the-box:

| Handler Name | Description | Example Response |
|--------------|-------------|------------------|
| `handle_help` | List commands | "Available commands: !help, !status, !race" |
| `handle_status` | Race status | "Race Status: In Progress \| Entrants: 4 (3 ready)" |
| `handle_race_info` | Goal/info | "Goal: Beat the game \| Info: Casual race" |
| `handle_time` | Finish time | "Your finish time: 1:23:45.67" |
| `handle_entrants` | List entrants | "Ready: Alice, Bob \| Not Ready: Charlie" |

## Features

### Cooldowns

Prevent spam:

```python
cooldown_seconds=30  # 30 second cooldown per user
```

### Linked Account Requirement

Some commands can require users to link their racetime account:

```python
require_linked_account=True
```

### Tournament Overrides

Override bot-wide commands for specific tournaments:

```python
# Bot-wide
await RacetimeChatCommand.create(
    command='rules',
    scope=CommandScope.BOT,
    response_text="General racing rules",
    racetime_bot_id=1,
)

# Tournament override
await RacetimeChatCommand.create(
    command='rules',
    scope=CommandScope.TOURNAMENT,
    response_text="Special rules for this tournament",
    tournament_id=5,
)
```

## Documentation

- **Full docs**: `docs/RACETIME_CHAT_COMMANDS.md`
- **Implementation details**: `docs/RACETIME_CHAT_COMMANDS_IMPLEMENTATION.md`
- **Handler development**: See `racetime/command_handlers.py`
- **Example script**: `tools/add_example_racetime_commands.py`

## Troubleshooting

### Command not responding

1. Check if command exists and is active:
   ```python
   cmd = await RacetimeChatCommand.filter(command='mycommand', is_active=True).first()
   ```

2. Check bot logs for errors:
   ```bash
   # Look for "Received command !mycommand" messages
   grep "command" logs/*.log
   ```

3. Verify bot is in the room and running

### Handler not found

Make sure handler is registered in `BUILTIN_HANDLERS` and the name matches exactly.

### Cooldown issues

Cooldowns are per-user. Different users can use the command independently.

## Next Steps

1. Add your own custom commands
2. Create tournament-specific command sets
3. Build a UI for command management (future enhancement)
4. Monitor command usage and analytics (future enhancement)

## Need Help?

See the full documentation in `docs/RACETIME_CHAT_COMMANDS.md` or check the implementation details in `docs/RACETIME_CHAT_COMMANDS_IMPLEMENTATION.md`.
