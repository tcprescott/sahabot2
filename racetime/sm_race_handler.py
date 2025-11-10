"""
Super Metroid RaceTime.gg handler.

This handler provides Super Metroid-specific chat commands for RaceTime.gg races.
Commands are defined in code using the ex_ prefix convention.
"""

import logging
from racetime.client import SahaRaceHandler
from application.services.randomizer.sm_service import SMService
from application.services.randomizer.sm_defaults import (
    get_varia_settings,
    get_dash_settings,
)

logger = logging.getLogger(__name__)


class SMRaceHandler(SahaRaceHandler):
    """
    Handler for Super Metroid races on RaceTime.gg.

    Extends SahaRaceHandler to add SM-specific commands:
    - !varia [preset] - Generate VARIA seed
    - !dash [preset] - Generate DASH seed
    - !total [preset] - Generate total randomization seed
    - !multiworld [preset] [players] - Generate multiworld seed
    """

    async def ex_varia(self, args, message):
        """
        Generate a VARIA seed with optional preset.

        Usage: !varia [preset]
        """
        try:
            service = SMService()

            # Parse preset name from args or use default
            preset_name = args[0] if args else "standard"

            # Get default settings for preset
            settings = get_varia_settings(preset_name)

            logger.info("Generating VARIA seed with preset %s", preset_name)

            result = await service.generate_varia(
                settings=settings, tournament=True, spoilers=False
            )

            await self.send_message(
                f"VARIA seed generated! {result.url} (Hash: {result.hash_id})"
            )

        except Exception as e:
            logger.error("Failed to generate VARIA seed: %s", str(e))
            await self.send_message(f"Failed to generate VARIA seed: {str(e)}")

    async def ex_dash(self, args, message):
        """
        Generate a DASH seed with optional preset.

        Usage: !dash [preset]
        """
        try:
            service = SMService()

            # Parse preset name from args or use default
            preset_name = args[0] if args else "standard"

            # Get default settings for preset
            settings = get_dash_settings(preset_name)

            logger.info("Generating DASH seed with preset %s", preset_name)

            result = await service.generate_dash(
                settings=settings, tournament=True, spoilers=False
            )

            await self.send_message(
                f"DASH seed generated! {result.url} (Hash: {result.hash_id})"
            )

        except Exception as e:
            logger.error("Failed to generate DASH seed: %s", str(e))
            await self.send_message(f"Failed to generate DASH seed: {str(e)}")

    async def ex_total(self, args, message):
        """
        Generate a DASH seed with full randomization (area + major/minor).

        Usage: !total [preset]
        """
        try:
            service = SMService()

            # Total randomization settings
            settings = {
                "preset": args[0] if args else "total",
                "area_rando": True,
                "major_minor_split": True,
                "boss_rando": True,
            }

            logger.info("Generating total randomization seed")

            result = await service.generate(
                settings=settings,
                randomizer_type="total",
                tournament=True,
                spoilers=False,
            )

            await self.send_message(
                f"Total randomization seed generated! {result.url} (Hash: {result.hash_id})"
            )

        except Exception as e:
            logger.error("Failed to generate total seed: %s", str(e))
            await self.send_message(f"Failed to generate total seed: {str(e)}")

    async def ex_multiworld(self, args, message):
        """
        Generate a multiworld seed for team races.

        Usage: !multiworld [preset] [player_count]
        """
        try:
            service = SMService()

            # Parse arguments
            preset_name = "default"
            player_count = 2

            if len(args) >= 1:
                # First arg could be preset or player count
                try:
                    player_count = int(args[0])
                except ValueError:
                    # First arg is preset name, not player count
                    preset_name = args[0]

            if len(args) >= 2:
                # Second arg is player count
                try:
                    player_count = int(args[1])
                except ValueError:
                    # If args[1] is not an integer, ignore and use default player_count
                    pass

            # Multiworld settings
            settings = {
                "preset": preset_name,
                "player_count": player_count,
                "multiworld": True,
            }

            logger.info("Generating multiworld seed for %s players", player_count)

            result = await service.generate(
                settings=settings,
                randomizer_type="multiworld",
                tournament=True,
                spoilers=False,
            )

            await self.send_message(
                f"Multiworld seed generated for {player_count} players! {result.url}"
            )

        except Exception as e:
            logger.error("Failed to generate multiworld seed: %s", str(e))
            await self.send_message(f"Failed to generate multiworld seed: {str(e)}")
