"""
ALTTPR-specific RaceTime.gg handler.

This handler provides ALTTPR-specific chat commands for RaceTime.gg races.
Commands are defined in code and registered with the @monitor_cmd decorator.
"""

import logging
from typing import Optional
from racetime_bot import monitor_cmd
from racetime.client import SahaRaceHandler
from models import User

logger = logging.getLogger(__name__)


class ALTTPRRaceHandler(SahaRaceHandler):
    """
    Handler for ALTTPR races on RaceTime.gg.
    
    Extends SahaRaceHandler to add ALTTPR-specific commands:
    - !mystery <preset> - Generate mystery seed from preset
    - !custommystery - Information about custom mystery
    """

    @monitor_cmd
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
    
    @monitor_cmd
    async def ex_custommystery(self, args, message):
        """
        Information about custom mystery weights.
        
        Usage: !custommystery
        """
        await self.send_message(
            "To use custom mystery weights, please upload your mystery YAML file via the web UI "
            "at /presets, then use !mystery <preset_name>"
        )
