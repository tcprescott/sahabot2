"""
ALTTPR-specific RaceTime.gg handler.

This handler provides ALTTPR-specific chat commands for RaceTime.gg races.
Commands are defined in code using the ex_ prefix convention.
"""

import logging
from typing import Optional
from racetime.client import SahaRaceHandler
from models import User

logger = logging.getLogger(__name__)


class ALTTPRRaceHandler(SahaRaceHandler):
    """
    Handler for ALTTPR races on RaceTime.gg.

    Extends SahaRaceHandler to add ALTTPR-specific commands:
    - !mystery <preset> - Generate mystery seed from preset
    - !custommystery - Information about custom mystery
    - !vt <preset> [branch] - Generate ALTTPR seed from preset
    - !vtspoiler <preset> [studytime] - Generate ALTTPR seed with spoiler log
    - !avianart <preset> - Generate Avianart door randomizer seed
    """

    async def ex_mystery(self, args, message):
        """
        Generate a mystery seed from a named mystery preset.

        Usage: !mystery <preset_name>
        """
        from application.services.randomizer.alttpr_mystery_service import ALTTPRMysteryService
        from application.repositories.user_repository import UserRepository

        # Extract racetime user info
        user_data = message.get('user', {})
        racetime_user_id = user_data.get('id', '')

        if not args:
            await self.send_message("Usage: !mystery <preset_name>")
            return

        # Look up application user (if racetime account is linked)
        user: Optional[User] = None
        try:
            user_repository = UserRepository()
            user = await user_repository.get_by_racetime_id(racetime_user_id)
        except Exception as e:
            logger.warning(
                "Error looking up user by racetime_id %s: %s", racetime_user_id, e
            )

        if not user:
            await self.send_message("You must be authenticated to generate mystery seeds.")
            return

        preset_name = args[0]

        try:
            service = ALTTPRMysteryService()
            result, description = await service.generate_from_preset_name(
                mystery_preset_name=preset_name,
                user_id=user.id,
                tournament=True,
                spoilers='off'
            )

            # Format description
            desc_parts = []
            if 'preset' in description:
                desc_parts.append(f"Preset: {description['preset']}")
            if 'subweight' in description:
                desc_parts.append(f"Subweight: {description['subweight']}")
            if 'entrance' in description and description['entrance'] != 'none':
                desc_parts.append(f"Entrance: {description['entrance']}")
            if 'customizer' in description:
                desc_parts.append("Customizer: enabled")

            desc_text = " | ".join(desc_parts) if desc_parts else "Mystery seed generated"

            await self.send_message(
                f"Mystery seed generated! {result.url} | {desc_text} | Hash: {result.hash_id}"
            )

        except ValueError as e:
            logger.error("Mystery generation error: %s", str(e))
            await self.send_message(f"Error: {str(e)}")
        except PermissionError as e:
            logger.error("Mystery permission error: %s", str(e))
            await self.send_message(f"Error: {str(e)}")
        except Exception as e:
            logger.exception("Unexpected error generating mystery seed")
            await self.send_message(f"An error occurred generating mystery seed: {str(e)}")

    async def ex_custommystery(self, args, message):
        """
        Information about custom mystery weights.

        Usage: !custommystery
        """
        await self.send_message(
            "To use custom mystery weights, please upload your mystery YAML file via the web UI "
            "at /presets, then use !mystery <preset_name>"
        )

    async def ex_vt(self, args, message):
        """
        Generate an ALTTPR seed from a preset (VT = vanilla tournament).

        Usage: !vt <preset_name> [branch]

        Args:
            preset_name: Name of the preset to use
            branch: Optional branch name (default: 'live')
        """
        from application.services.randomizer.alttpr_service import ALTTPRService
        from application.repositories.user_repository import UserRepository

        # Extract racetime user info
        user_data = message.get('user', {})
        racetime_user_id = user_data.get('id', '')

        if not args:
            await self.send_message("Usage: !vt <preset_name> [branch]")
            return

        # Look up application user (if racetime account is linked)
        user: Optional[User] = None
        try:
            user_repository = UserRepository()
            user = await user_repository.get_by_racetime_id(racetime_user_id)
        except Exception as e:
            logger.warning(
                "Error looking up user by racetime_id %s: %s", racetime_user_id, e
            )

        if not user:
            await self.send_message("You must be authenticated to generate seeds.")
            return

        preset_name = args[0]

        # Optional branch parameter (not currently used in sahabot2, but preserving API)
        # branch = args[1] if len(args) > 1 else 'live'

        await self.send_message("Generating game, please wait. If nothing happens after a minute, contact support.")

        try:
            service = ALTTPRService()
            result = await service.generate_from_preset(
                preset_name=preset_name,
                user_id=user.id,
                tournament=True,
                spoilers='off',
                allow_quickswap=True
            )

            # Format race info
            race_info = f"{preset_name} - {result.url}"
            if result.hash_id and result.hash_id != 'unknown':
                race_info += f" - ({result.hash_id})"

            await self.send_message(result.url)
            await self.send_message(f"Seed rolling complete. {race_info}")

        except ValueError as e:
            logger.error("Preset error: %s", str(e))
            await self.send_message(f"Error: {str(e)}")
        except PermissionError as e:
            logger.error("Permission error: %s", str(e))
            await self.send_message(f"Error: {str(e)}")
        except Exception as e:
            logger.exception("Unexpected error generating seed")
            await self.send_message(f"An error occurred generating seed: {str(e)}")

    async def ex_vtspoiler(self, args, message):
        """
        Generate an ALTTPR seed with spoiler log.

        Usage: !vtspoiler <preset_name> [studytime]

        Args:
            preset_name: Name of the preset to use
            studytime: Optional study time in seconds (default: 900)
        """
        from application.services.randomizer.alttpr_service import ALTTPRService
        from application.repositories.user_repository import UserRepository

        # Extract racetime user info
        user_data = message.get('user', {})
        racetime_user_id = user_data.get('id', '')

        if not args:
            await self.send_message("Usage: !vtspoiler <preset_name> [studytime]")
            return

        # Look up application user (if racetime account is linked)
        user: Optional[User] = None
        try:
            user_repository = UserRepository()
            user = await user_repository.get_by_racetime_id(racetime_user_id)
        except Exception as e:
            logger.warning(
                "Error looking up user by racetime_id %s: %s", racetime_user_id, e
            )

        if not user:
            await self.send_message("You must be authenticated to generate seeds.")
            return

        preset_name = args[0]

        # Optional studytime parameter
        try:
            studytime = int(args[1]) if len(args) > 1 else 900
        except (ValueError, IndexError):
            studytime = 900

        await self.send_message("Generating game, please wait. If nothing happens after a minute, contact support.")

        try:
            service = ALTTPRService()
            result = await service.generate_from_preset(
                preset_name=preset_name,
                user_id=user.id,
                tournament=True,
                spoilers='on',  # Generate with spoiler log
                allow_quickswap=False
            )

            # Format race info
            race_info = f"spoiler {preset_name} - {result.url}"
            if result.hash_id and result.hash_id != 'unknown':
                race_info += f" - ({result.hash_id})"

            await self.send_message(result.url)

            if result.spoiler_url:
                await self.send_message(
                    f"The spoiler log for this race: {result.spoiler_url}"
                )
                await self.send_message(
                    f"A {studytime}s study time is recommended before starting the race."
                )
            else:
                await self.send_message("Note: Spoiler log generation may not be available.")

            await self.send_message(f"Seed rolling complete. {race_info}")

        except ValueError as e:
            logger.error("Preset error: %s", str(e))
            await self.send_message(f"Error: {str(e)}")
        except PermissionError as e:
            logger.error("Permission error: %s", str(e))
            await self.send_message(f"Error: {str(e)}")
        except Exception as e:
            logger.exception("Unexpected error generating seed")
            await self.send_message(f"An error occurred generating seed: {str(e)}")

    async def ex_avianart(self, args, message):
        """
        Generate an Avianart door randomizer seed.

        Usage: !avianart <preset_name>

        Args:
            preset_name: Name of the Avianart preset to use

        Note:
            This command does NOT require user authentication (unlike !mystery, !vt, !vtspoiler).
            Avianart uses API preset names directly without database lookup, so any race
            participant can use it. This is intentional per the design requirements.
        """
        from application.services.randomizer.avianart_service import AvianartService

        if not args:
            await self.send_message("Usage: !avianart <preset_name>")
            return

        preset_name = args[0]

        await self.send_message("Generating Avianart seed, please wait. If nothing happens after a minute, contact support.")

        try:
            service = AvianartService()
            result = await service.generate(
                preset=preset_name,
                race=True
            )

            # Extract file select code and format it
            file_select_code = result.metadata.get('file_select_code', [])
            code_str = '/'.join(file_select_code)

            # Extract version
            version = result.metadata.get('version', 'unknown')

            await self.send_message(
                f"Avianart seed generated! {result.url} | "
                f"Code: {code_str} | Version: {version}"
            )

        except ValueError as e:
            logger.error("Avianart preset error: %s", str(e))
            await self.send_message(f"Error: {str(e)}")
        except TimeoutError as e:
            logger.error("Avianart timeout: %s", str(e))
            await self.send_message("Seed generation timed out. Please try again or contact support.")
        except Exception as e:
            logger.exception("Unexpected error generating Avianart seed")
            await self.send_message(f"An error occurred generating Avianart seed: {str(e)}")
