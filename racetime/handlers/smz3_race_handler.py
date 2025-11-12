"""
SMZ3-specific RaceTime.gg handler.

This handler provides SMZ3-specific chat commands for RaceTime.gg races.
Commands are defined in code using the ex_ prefix convention.
"""

import logging

from racetime.handlers.base_handler import SahaRaceHandler
from application.services.randomizer.smz3_service import (
    SMZ3Service,
    DEFAULT_SMZ3_SETTINGS,
)

logger = logging.getLogger(__name__)


class SMZ3RaceHandler(SahaRaceHandler):
    """
    Handler for SMZ3 races on RaceTime.gg.

    Extends SahaRaceHandler to add SMZ3-specific commands:
    - !race [preset] - Generate SMZ3 seed with optional preset
    - !preset <name> - Generate seed using a specific preset
    - !spoiler [preset] - Generate seed with spoiler log
    """

    async def ex_race(self, args, message):
        """
        Generate an SMZ3 seed with optional preset.

        Usage: !race [preset]
        """
        try:
            smz3_service = SMZ3Service()
            from application.repositories.randomizer_preset_repository import (
                RandomizerPresetRepository,
            )

            preset_repository = RandomizerPresetRepository()

            # Start with default settings
            settings = DEFAULT_SMZ3_SETTINGS.copy()

            # If preset specified, load it
            preset_name = None
            if args:
                preset_name = args[0]
                try:
                    preset = await preset_repository.get_global_preset(
                        randomizer="smz3", name=preset_name
                    )
                    if preset and preset.settings:
                        # Merge preset settings with defaults
                        settings.update(preset.settings)
                        logger.info("Loaded SMZ3 preset: %s", preset_name)
                    else:
                        await self.send_message(
                            f"Preset '{preset_name}' not found. Using default settings."
                        )
                        preset_name = None
                except Exception as e:
                    logger.error("Error loading preset %s: %s", preset_name, e)
                    await self.send_message(
                        f"Error loading preset '{preset_name}'. Using default settings."
                    )
                    preset_name = None

            # Generate seed
            result = await smz3_service.generate(
                settings=settings, tournament=True, spoilers=False
            )

            # Format response
            race_data = self.data if self.data else {}
            goal_name = race_data.get("goal", {}).get("name", "SMZ3")
            response = f"SMZ3 Seed Generated! | {goal_name} | {result.url}"

            # Add preset info if used
            if preset_name:
                response = f"{response} | Preset: {preset_name}"

            await self.send_message(response)

        except Exception as e:
            logger.error("Error generating SMZ3 seed: %s", e, exc_info=True)
            await self.send_message(f"Error generating seed: {str(e)}")

    async def ex_preset(self, args, message):
        """
        Generate an SMZ3 seed using a specific preset.

        Usage: !preset <name>
        """
        if not args:
            await self.send_message("Usage: !preset <name> - Specify a preset name")
            return

        # Delegate to race command with preset argument
        await self.ex_race(args, message)

    async def ex_spoiler(self, args, message):
        """
        Generate an SMZ3 seed with spoiler log access.

        Usage: !spoiler [preset]
        """
        try:
            smz3_service = SMZ3Service()
            from application.repositories.randomizer_preset_repository import (
                RandomizerPresetRepository,
            )

            preset_repository = RandomizerPresetRepository()

            # Start with default settings
            settings = DEFAULT_SMZ3_SETTINGS.copy()

            # If preset specified, load it
            preset_name = None
            if args:
                preset_name = args[0]
                try:
                    preset = await preset_repository.get_global_preset(
                        randomizer="smz3", name=preset_name
                    )
                    if preset and preset.settings:
                        settings.update(preset.settings)
                        logger.info("Loaded SMZ3 preset for spoiler: %s", preset_name)
                except Exception as e:
                    logger.error("Error loading preset %s: %s", preset_name, e)

            # Generate seed with spoilers (don't pass spoiler_key - not supported by service)
            result = await smz3_service.generate(
                settings=settings,
                tournament=False,  # Non-tournament mode for spoilers
                spoilers=True,
            )

            # Format response
            response = f"SMZ3 Seed with Spoiler | {result.url}"

            if result.spoiler_url:
                response = f"{response} | Spoiler: {result.spoiler_url}"

            if preset_name:
                response = f"{response} | Preset: {preset_name}"

            await self.send_message(response)

        except Exception as e:
            logger.error("Error generating SMZ3 spoiler seed: %s", e, exc_info=True)
            await self.send_message(f"Error generating seed: {str(e)}")
