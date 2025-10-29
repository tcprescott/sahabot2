# Discord Bot Commands

This directory contains all Discord bot application commands for SahaBot2.

## Structure

Commands are organized into cogs (command groups) based on functionality:

- `test_commands.py` - Simple test commands for verifying bot functionality

## Creating New Commands

To add new commands:

1. Create a new file in this directory (e.g., `user_commands.py`)
2. Define a Cog class that inherits from `commands.Cog`
3. Use `@app_commands.command()` decorator for slash commands
4. Implement a `setup(bot)` async function to register the cog
5. Load the extension in `bot/client.py` setup_hook

### Example

```python
import discord
from discord import app_commands
from discord.ext import commands

class MyCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
    
    @app_commands.command(name="mycommand", description="My command description")
    async def my_command(self, interaction: discord.Interaction):
        """Command implementation."""
        await interaction.response.send_message("Hello!", ephemeral=True)

async def setup(bot: commands.Bot):
    await bot.add_cog(MyCog(bot))
```

## Important Rules

1. **Application Commands Only**: Always use `@app_commands.command()` for slash commands. Never use prefix-based commands.
2. **Use Services**: Delegate all business logic to the service layer. Never access ORM models directly.
3. **Presentation Layer**: Bot commands should only handle Discord interactions (parsing input, formatting responses).
4. **Logging**: Log command invocations and errors for debugging.
5. **Error Handling**: Handle errors gracefully and provide user-friendly error messages.

## Current Commands

### Test Commands

- `/test` - Simple test command that verifies the bot is working correctly. Returns an embed with user information.

## Testing

To test commands:

1. Ensure the bot is running (`./start.sh dev`)
2. In Discord, type `/` to see available commands
3. Select the command and execute it
4. Check application logs for any errors

## Syncing Commands

Commands are automatically synced to Discord when the bot starts up. If you add new commands and they don't appear:

1. Restart the application
2. Wait a few minutes for Discord to update the command cache
3. If still not appearing, check logs for sync errors
