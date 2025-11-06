"""
SMZ3-specific RaceTime.gg handler commands.

This module provides SMZ3-specific chat command handlers for RaceTime.gg races.
These handlers can be registered with the command service to enable SMZ3 seed generation
in SMZ3 category race rooms.

Commands:
- !race [preset] - Generate an SMZ3 seed with optional preset
- !preset [name] - Generate seed using a specific preset
- !spoiler [preset] - Generate seed with spoiler log
"""

import logging
from typing import Optional
from models import User, RacetimeChatCommand
from application.services.randomizer.smz3_service import SMZ3Service
from application.services.randomizer.randomizer_preset_service import RandomizerPresetService

logger = logging.getLogger(__name__)


async def handle_smz3_race(
    _command: RacetimeChatCommand,
    args: list[str],
    _racetime_user_id: str,
    race_data: dict,
    _user: Optional[User],
) -> str:
    """
    Handle the !race command for SMZ3.

    Generates an SMZ3 seed with optional preset.

    Usage:
        !race - Generate default SMZ3 seed
        !race [preset] - Generate seed with specified preset

    Args:
        _command: The command model
        args: Command arguments (optional preset name)
        _racetime_user_id: RaceTime.gg user ID
        race_data: Current race data
        _user: Application user (if linked)

    Returns:
        str: Response message with seed URL
    """
    try:
        smz3_service = SMZ3Service()
        preset_service = RandomizerPresetService()

        # Default settings for SMZ3
        settings = {
            'logic': 'normal',
            'mode': 'normal',
            'goal': 'defeatBoth',
            'itemPlacement': 'major',
            'swordLocation': 'randomized',
            'morphLocation': 'original',
        }

        # If preset specified, load it
        if args:
            preset_name = args[0]
            try:
                preset = await preset_service.get_preset_by_name(
                    randomizer='smz3',
                    name=preset_name
                )
                if preset and preset.settings:
                    # Merge preset settings with defaults
                    settings.update(preset.settings)
                    logger.info("Loaded SMZ3 preset: %s", preset_name)
                else:
                    return f"Preset '{preset_name}' not found. Using default settings."
            except Exception as e:
                logger.error("Error loading preset %s: %s", preset_name, e)
                return f"Error loading preset '{preset_name}'. Using default settings."

        # Generate seed
        result = await smz3_service.generate(
            settings=settings,
            tournament=True,
            spoilers=False
        )

        # Format response
        goal_name = race_data.get('goal', {}).get('name', 'SMZ3')
        response = f"SMZ3 Seed Generated! | {goal_name} | {result.url}"

        # Add preset info if used
        if args:
            response = f"{response} | Preset: {args[0]}"

        return response

    except Exception as e:
        logger.error("Error generating SMZ3 seed: %s", e, exc_info=True)
        return f"Error generating seed: {str(e)}"


async def handle_smz3_preset(
    _command: RacetimeChatCommand,
    args: list[str],
    _racetime_user_id: str,
    race_data: dict,
    _user: Optional[User],
) -> str:
    """
    Handle the !preset command for SMZ3.

    Generates an SMZ3 seed using a specific preset.

    Usage:
        !preset [name] - Generate seed with specified preset

    Args:
        _command: The command model
        args: Command arguments (required preset name)
        _racetime_user_id: RaceTime.gg user ID
        race_data: Current race data
        _user: Application user (if linked)

    Returns:
        str: Response message with seed URL
    """
    if not args:
        return "Usage: !preset [name] - Specify a preset name"

    # Delegate to race handler with preset argument
    return await handle_smz3_race(_command, args, _racetime_user_id, race_data, _user)


async def handle_smz3_spoiler(
    _command: RacetimeChatCommand,
    args: list[str],
    _racetime_user_id: str,
    race_data: dict,
    _user: Optional[User],
) -> str:
    """
    Handle the !spoiler command for SMZ3.

    Generates an SMZ3 seed with spoiler log access.

    Usage:
        !spoiler - Generate seed with spoiler log
        !spoiler [preset] - Generate seed with preset and spoiler log

    Args:
        _command: The command model
        args: Command arguments (optional preset name)
        _racetime_user_id: RaceTime.gg user ID
        race_data: Current race data
        _user: Application user (if linked)

    Returns:
        str: Response message with seed URL and spoiler URL
    """
    try:
        smz3_service = SMZ3Service()
        preset_service = RandomizerPresetService()

        # Default settings for SMZ3
        settings = {
            'logic': 'normal',
            'mode': 'normal',
            'goal': 'defeatBoth',
            'itemPlacement': 'major',
            'swordLocation': 'randomized',
            'morphLocation': 'original',
        }

        # If preset specified, load it
        preset_name = None
        if args:
            preset_name = args[0]
            try:
                preset = await preset_service.get_preset_by_name(
                    randomizer='smz3',
                    name=preset_name
                )
                if preset and preset.settings:
                    settings.update(preset.settings)
                    logger.info("Loaded SMZ3 preset for spoiler: %s", preset_name)
            except Exception as e:
                logger.error("Error loading preset %s: %s", preset_name, e)

        # Generate seed with spoiler key
        spoiler_key = "spoiler"  # Simple spoiler key
        result = await smz3_service.generate(
            settings=settings,
            tournament=False,  # Non-tournament mode for spoilers
            spoilers=True,
            spoiler_key=spoiler_key
        )

        # Format response
        response = f"SMZ3 Seed with Spoiler | {result.url}"

        if result.spoiler_url:
            response = f"{response} | Spoiler: {result.spoiler_url}"

        if preset_name:
            response = f"{response} | Preset: {preset_name}"

        return response

    except Exception as e:
        logger.error("Error generating SMZ3 spoiler seed: %s", e, exc_info=True)
        return f"Error generating seed: {str(e)}"


# Registry of SMZ3-specific handlers
SMZ3_HANDLERS = {
    'handle_smz3_race': handle_smz3_race,
    'handle_smz3_preset': handle_smz3_preset,
    'handle_smz3_spoiler': handle_smz3_spoiler,
}
