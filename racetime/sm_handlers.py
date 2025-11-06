"""
Super Metroid randomizer command handlers for RaceTime.gg.

This module provides handlers for SM-specific chat commands in RaceTime.gg race rooms.
Supports VARIA, DASH, and multiworld seed generation.
"""

import logging
from typing import Optional, Dict, Any
from models import User, RacetimeChatCommand
from application.services.randomizer.sm_service import SMService

logger = logging.getLogger(__name__)


async def handle_varia(
    command: RacetimeChatCommand,
    args: list[str],
    racetime_user_id: str,
    race_data: dict,
    user: Optional[User],
) -> str:
    """
    Handle the !varia command.

    Generates a VARIA seed with optional preset.

    Args:
        command: The command configuration
        args: Command arguments (preset name or settings)
        racetime_user_id: RaceTime.gg user ID
        race_data: Current race data
        user: Linked user account (if available)

    Returns:
        Response message with seed URL
    """
    try:
        service = SMService()

        # Parse preset name from args or use default
        preset_name = args[0] if args else 'default'

        # TODO: Load preset from database when preset system is integrated
        # For now, use basic default settings
        settings = {
            'preset': preset_name,
            'logic': 'casual',
            'itemProgression': 'normal',
            'morphPlacement': 'early',
        }

        logger.info("Generating VARIA seed with preset %s", preset_name)

        result = await service.generate_varia(
            settings=settings,
            tournament=True,
            spoilers=False
        )

        return f"VARIA seed generated! {result.url} (Hash: {result.hash_id})"

    except Exception as e:
        logger.error("Failed to generate VARIA seed: %s", str(e))
        return f"Failed to generate VARIA seed: {str(e)}"


async def handle_dash(
    command: RacetimeChatCommand,
    args: list[str],
    racetime_user_id: str,
    race_data: dict,
    user: Optional[User],
) -> str:
    """
    Handle the !dash command.

    Generates a DASH seed with optional preset.

    Args:
        command: The command configuration
        args: Command arguments (preset name or settings)
        racetime_user_id: RaceTime.gg user ID
        race_data: Current race data
        user: Linked user account (if available)

    Returns:
        Response message with seed URL
    """
    try:
        service = SMService()

        # Parse preset name from args or use default
        preset_name = args[0] if args else 'default'

        # TODO: Load preset from database when preset system is integrated
        # For now, use basic default settings
        settings = {
            'preset': preset_name,
            'area_rando': False,
            'major_minor_split': True,
        }

        logger.info("Generating DASH seed with preset %s", preset_name)

        result = await service.generate_dash(
            settings=settings,
            tournament=True,
            spoilers=False
        )

        return f"DASH seed generated! {result.url} (Hash: {result.hash_id})"

    except Exception as e:
        logger.error("Failed to generate DASH seed: %s", str(e))
        return f"Failed to generate DASH seed: {str(e)}"


async def handle_total(
    command: RacetimeChatCommand,
    args: list[str],
    racetime_user_id: str,
    race_data: dict,
    user: Optional[User],
) -> str:
    """
    Handle the !total command.

    Generates a DASH seed with full randomization (area + major/minor).

    Args:
        command: The command configuration
        args: Command arguments (optional)
        racetime_user_id: RaceTime.gg user ID
        race_data: Current race data
        user: Linked user account (if available)

    Returns:
        Response message with seed URL
    """
    try:
        service = SMService()

        # Total randomization settings
        settings = {
            'preset': args[0] if args else 'total',
            'area_rando': True,
            'major_minor_split': True,
            'boss_rando': True,
        }

        logger.info("Generating total randomization seed")

        result = await service.generate(
            settings=settings,
            randomizer_type='total',
            tournament=True,
            spoilers=False
        )

        return f"Total randomization seed generated! {result.url} (Hash: {result.hash_id})"

    except Exception as e:
        logger.error("Failed to generate total seed: %s", str(e))
        return f"Failed to generate total seed: {str(e)}"


async def handle_multiworld(
    command: RacetimeChatCommand,
    args: list[str],
    racetime_user_id: str,
    race_data: dict,
    user: Optional[User],
) -> str:
    """
    Handle the !multiworld command.

    Generates a multiworld seed for team races.

    Args:
        command: The command configuration
        args: Command arguments (preset name and player count)
        racetime_user_id: RaceTime.gg user ID
        race_data: Current race data
        user: Linked user account (if available)

    Returns:
        Response message with seed URL
    """
    try:
        service = SMService()

        # Parse arguments
        preset_name = 'default'
        player_count = 2

        if len(args) >= 1:
            # First arg could be preset or player count
            try:
                player_count = int(args[0])
            except ValueError:
                preset_name = args[0]

        if len(args) >= 2:
            # Second arg is player count
            try:
                player_count = int(args[1])
            except ValueError:
                pass

        # Multiworld settings
        settings = {
            'preset': preset_name,
            'player_count': player_count,
            'multiworld': True,
        }

        logger.info("Generating multiworld seed for %s players", player_count)

        result = await service.generate(
            settings=settings,
            randomizer_type='multiworld',
            tournament=True,
            spoilers=False
        )

        return f"Multiworld seed generated for {player_count} players! {result.url}"

    except Exception as e:
        logger.error("Failed to generate multiworld seed: %s", str(e))
        return f"Failed to generate multiworld seed: {str(e)}"


# Registry of SM-specific handlers
SM_HANDLERS = {
    'handle_varia': handle_varia,
    'handle_dash': handle_dash,
    'handle_total': handle_total,
    'handle_multiworld': handle_multiworld,
}
