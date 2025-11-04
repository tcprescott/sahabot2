"""
Utility script to add example racetime chat commands to the database.

This demonstrates how to create bot-level and tournament-level commands.
"""

import asyncio
import logging
from tortoise import Tortoise
from models import RacetimeChatCommand, CommandScope, CommandResponseType, RacetimeBot
from config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def add_example_commands():
    """Add example chat commands for demonstration."""
    
    # Initialize database
    await Tortoise.init(
        db_url=settings.DATABASE_URL,
        modules={'models': ['models']},
    )
    await Tortoise.generate_schemas()
    
    try:
        # Get a bot (assuming alttpr bot exists)
        bot = await RacetimeBot.filter(category='alttpr').first()
        
        if not bot:
            logger.error("No ALTTPR bot found. Please create a bot first.")
            return
        
        logger.info("Found bot: %s (ID: %s)", bot.name, bot.id)
        
        # Example 1: Simple text response command (bot-level)
        help_cmd = await RacetimeChatCommand.filter(
            racetime_bot_id=bot.id, command='help'
        ).first()
        
        if not help_cmd:
            help_cmd = await RacetimeChatCommand.create(
                command='help',
                description='Display available commands',
                scope=CommandScope.BOT,
                response_type=CommandResponseType.DYNAMIC,
                handler_name='handle_help',
                racetime_bot_id=bot.id,
                is_active=True,
            )
            logger.info("Created command: !help")
        else:
            logger.info("Command !help already exists")
        
        # Example 2: Race status command (dynamic handler)
        status_cmd = await RacetimeChatCommand.filter(
            racetime_bot_id=bot.id, command='status'
        ).first()
        
        if not status_cmd:
            status_cmd = await RacetimeChatCommand.create(
                command='status',
                description='Display current race status',
                scope=CommandScope.BOT,
                response_type=CommandResponseType.DYNAMIC,
                handler_name='handle_status',
                racetime_bot_id=bot.id,
                is_active=True,
            )
            logger.info("Created command: !status")
        else:
            logger.info("Command !status already exists")
        
        # Example 3: Race info command
        race_cmd = await RacetimeChatCommand.filter(
            racetime_bot_id=bot.id, command='race'
        ).first()
        
        if not race_cmd:
            race_cmd = await RacetimeChatCommand.create(
                command='race',
                description='Display race goal and info',
                scope=CommandScope.BOT,
                response_type=CommandResponseType.DYNAMIC,
                handler_name='handle_race_info',
                racetime_bot_id=bot.id,
                is_active=True,
            )
            logger.info("Created command: !race")
        else:
            logger.info("Command !race already exists")
        
        # Example 4: Simple text response with cooldown
        rules_cmd = await RacetimeChatCommand.filter(
            racetime_bot_id=bot.id, command='rules'
        ).first()
        
        if not rules_cmd:
            rules_cmd = await RacetimeChatCommand.create(
                command='rules',
                description='Display tournament rules',
                scope=CommandScope.BOT,
                response_type=CommandResponseType.TEXT,
                response_text=(
                    "Tournament Rules: 1) Be respectful. "
                    "2) Follow the seed settings. "
                    "3) Have fun! "
                    "Full rules: https://example.com/rules"
                ),
                racetime_bot_id=bot.id,
                cooldown_seconds=30,  # 30 second cooldown
                is_active=True,
            )
            logger.info("Created command: !rules (with 30s cooldown)")
        else:
            logger.info("Command !rules already exists")
        
        # Example 5: Entrants list command
        entrants_cmd = await RacetimeChatCommand.filter(
            racetime_bot_id=bot.id, command='entrants'
        ).first()
        
        if not entrants_cmd:
            entrants_cmd = await RacetimeChatCommand.create(
                command='entrants',
                description='List race entrants and their statuses',
                scope=CommandScope.BOT,
                response_type=CommandResponseType.DYNAMIC,
                handler_name='handle_entrants',
                racetime_bot_id=bot.id,
                is_active=True,
            )
            logger.info("Created command: !entrants")
        else:
            logger.info("Command !entrants already exists")
        
        logger.info("Example commands setup complete!")
        logger.info("Try these commands in a racetime room:")
        logger.info("  !help - Display available commands")
        logger.info("  !status - Show race status")
        logger.info("  !race - Show race goal and info")
        logger.info("  !rules - Display tournament rules (30s cooldown)")
        logger.info("  !entrants - List all entrants")
        
    finally:
        await Tortoise.close_connections()


if __name__ == '__main__':
    asyncio.run(add_example_commands())
