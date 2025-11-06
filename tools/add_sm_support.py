"""
Utility script to add Super Metroid chat commands and example presets.

This script adds SM-specific commands for RaceTime.gg bots and example presets
for VARIA and DASH randomizers.
"""

import asyncio
import logging
from tortoise import Tortoise
from models import (
    RacetimeChatCommand,
    CommandScope,
    CommandResponseType,
    RacetimeBot,
    RandomizerPreset,
    PresetNamespace,
    User
)
from config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def add_sm_commands():
    """Add SM-specific chat commands to SM category bots."""

    # Initialize database
    await Tortoise.init(
        db_url=settings.DATABASE_URL,
        modules={'models': ['models']},
    )
    await Tortoise.generate_schemas()

    try:
        # Get SM bots (smvaria, smdash, smtotal categories)
        bots = await RacetimeBot.filter(
            category__in=['smvaria', 'smdash', 'smtotal', 'sm']
        ).all()

        if not bots:
            logger.warning("No SM bots found. Commands will need to be added later.")
            logger.info("To add SM bots, create them via the admin panel first.")
        else:
            for bot in bots:
                logger.info("Found bot: %s (Category: %s)", bot.name, bot.category)

                # Add !varia command
                varia_cmd = await RacetimeChatCommand.filter(
                    racetime_bot_id=bot.id, command='varia'
                ).first()

                if not varia_cmd:
                    await RacetimeChatCommand.create(
                        command='varia',
                        description='Generate a VARIA randomizer seed',
                        scope=CommandScope.BOT,
                        response_type=CommandResponseType.DYNAMIC,
                        handler_name='handle_varia',
                        racetime_bot_id=bot.id,
                        is_active=True,
                    )
                    logger.info("Created command: !varia for bot %s", bot.name)

                # Add !dash command
                dash_cmd = await RacetimeChatCommand.filter(
                    racetime_bot_id=bot.id, command='dash'
                ).first()

                if not dash_cmd:
                    await RacetimeChatCommand.create(
                        command='dash',
                        description='Generate a DASH randomizer seed',
                        scope=CommandScope.BOT,
                        response_type=CommandResponseType.DYNAMIC,
                        handler_name='handle_dash',
                        racetime_bot_id=bot.id,
                        is_active=True,
                    )
                    logger.info("Created command: !dash for bot %s", bot.name)

                # Add !total command
                total_cmd = await RacetimeChatCommand.filter(
                    racetime_bot_id=bot.id, command='total'
                ).first()

                if not total_cmd:
                    await RacetimeChatCommand.create(
                        command='total',
                        description='Generate a total randomization seed',
                        scope=CommandScope.BOT,
                        response_type=CommandResponseType.DYNAMIC,
                        handler_name='handle_total',
                        racetime_bot_id=bot.id,
                        is_active=True,
                    )
                    logger.info("Created command: !total for bot %s", bot.name)

                # Add !multiworld command
                multiworld_cmd = await RacetimeChatCommand.filter(
                    racetime_bot_id=bot.id, command='multiworld'
                ).first()

                if not multiworld_cmd:
                    await RacetimeChatCommand.create(
                        command='multiworld',
                        description='Generate a multiworld seed for team races',
                        scope=CommandScope.BOT,
                        response_type=CommandResponseType.DYNAMIC,
                        handler_name='handle_multiworld',
                        racetime_bot_id=bot.id,
                        is_active=True,
                    )
                    logger.info("Created command: !multiworld for bot %s", bot.name)

        logger.info("\n=== SM Commands Setup Complete ===")
        logger.info("Available commands in SM race rooms:")
        logger.info("  !varia [preset] - Generate VARIA seed")
        logger.info("  !dash [preset] - Generate DASH seed")
        logger.info("  !total [preset] - Generate total randomization seed")
        logger.info("  !multiworld [preset] [players] - Generate multiworld seed")

    finally:
        await Tortoise.close_connections()


async def add_sm_example_presets():
    """Add example SM presets for VARIA and DASH."""

    # Initialize database
    await Tortoise.init(
        db_url=settings.DATABASE_URL,
        modules={'models': ['models']},
    )
    await Tortoise.generate_schemas()

    try:
        # Get or create a system user for preset creation
        system_user = await User.filter(discord_username='System').first()

        if not system_user:
            logger.warning("No system user found. Using first admin user.")
            from models import Permission
            system_user = await User.filter(permission=Permission.ADMIN).first()

        if not system_user:
            logger.error("No suitable user found for preset creation. Please create a user first.")
            return

        logger.info("Using user: %s (ID: %s)", system_user.discord_username, system_user.id)

        # Get or create global namespace
        global_namespace = await PresetNamespace.filter(name='global').first()

        if not global_namespace:
            global_namespace = await PresetNamespace.create(
                name='global',
                display_name='Global Presets',
                description='System-wide preset library',
                is_public=True
            )
            logger.info("Created global namespace")

        # VARIA Presets
        varia_presets = [
            {
                'name': 'casual',
                'description': 'VARIA Casual difficulty preset',
                'settings': {
                    'logic': 'casual',
                    'itemProgression': 'normal',
                    'morphPlacement': 'early',
                    'progressionSpeed': 'medium',
                    'energyQty': 'normal'
                }
            },
            {
                'name': 'master',
                'description': 'VARIA Master difficulty preset',
                'settings': {
                    'logic': 'master',
                    'itemProgression': 'fast',
                    'morphPlacement': 'random',
                    'progressionSpeed': 'fast',
                    'energyQty': 'low'
                }
            },
            {
                'name': 'expert',
                'description': 'VARIA Expert difficulty preset',
                'settings': {
                    'logic': 'expert',
                    'itemProgression': 'fast',
                    'morphPlacement': 'random',
                    'progressionSpeed': 'veryfast',
                    'energyQty': 'verylow'
                }
            },
        ]

        for preset_data in varia_presets:
            existing = await RandomizerPreset.filter(
                namespace_id=global_namespace.id,
                randomizer='sm-varia',
                name=preset_data['name']
            ).first()

            if not existing:
                await RandomizerPreset.create(
                    namespace_id=global_namespace.id,
                    user_id=system_user.id,
                    randomizer='sm-varia',
                    name=preset_data['name'],
                    description=preset_data['description'],
                    settings=preset_data['settings'],
                    is_public=True
                )
                logger.info("Created VARIA preset: %s", preset_data['name'])
            else:
                logger.info("VARIA preset %s already exists", preset_data['name'])

        # DASH Presets
        dash_presets = [
            {
                'name': 'standard',
                'description': 'DASH Standard preset',
                'settings': {
                    'area_rando': False,
                    'major_minor_split': True,
                    'boss_rando': False,
                    'item_progression': 'normal'
                }
            },
            {
                'name': 'area',
                'description': 'DASH with area randomization',
                'settings': {
                    'area_rando': True,
                    'major_minor_split': True,
                    'boss_rando': False,
                    'item_progression': 'normal'
                }
            },
            {
                'name': 'total',
                'description': 'DASH total randomization',
                'settings': {
                    'area_rando': True,
                    'major_minor_split': True,
                    'boss_rando': True,
                    'item_progression': 'fast'
                }
            },
        ]

        for preset_data in dash_presets:
            existing = await RandomizerPreset.filter(
                namespace_id=global_namespace.id,
                randomizer='sm-dash',
                name=preset_data['name']
            ).first()

            if not existing:
                await RandomizerPreset.create(
                    namespace_id=global_namespace.id,
                    user_id=system_user.id,
                    randomizer='sm-dash',
                    name=preset_data['name'],
                    description=preset_data['description'],
                    settings=preset_data['settings'],
                    is_public=True
                )
                logger.info("Created DASH preset: %s", preset_data['name'])
            else:
                logger.info("DASH preset %s already exists", preset_data['name'])

        logger.info("\n=== SM Presets Setup Complete ===")
        logger.info("VARIA presets: casual, master, expert")
        logger.info("DASH presets: standard, area, total")
        logger.info("Presets available in global namespace")

    finally:
        await Tortoise.close_connections()


async def main():
    """Main function to setup SM commands and presets."""
    logger.info("=== Setting up Super Metroid Support ===\n")

    logger.info("Step 1: Adding SM chat commands...")
    await add_sm_commands()

    logger.info("\nStep 2: Adding SM example presets...")
    await add_sm_example_presets()

    logger.info("\n=== Setup Complete ===")


if __name__ == '__main__':
    asyncio.run(main())
