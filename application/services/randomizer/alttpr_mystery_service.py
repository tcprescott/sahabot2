"""
A Link to the Past Randomizer Mystery service.

This service handles generation of mystery seeds with weighted preset selection.
Mystery seeds randomly select presets and settings based on configured weights.
"""

import logging
import random
from typing import Dict, Any, Optional, List, Tuple
from .alttpr_service import ALTTPRService
from .randomizer_service import RandomizerResult

logger = logging.getLogger(__name__)


class ALTTPRMysteryService:
    """
    Service for ALTTPR mystery seed generation.

    Mystery seeds use weighted selection to randomly choose:
    - Presets (main settings)
    - Subweights (conditional/nested settings)
    - Entrance shuffle options
    - Customizer settings (eq, custom, timed-ohko, triforce-hunt, pool sections)
    """

    def __init__(self):
        """Initialize the ALTTPR mystery service."""
        self.alttpr_service = ALTTPRService()

    async def generate_from_mystery_weights(
        self,
        mystery_weights: Dict[str, Any],
        tournament: bool = True,
        spoilers: str = "off",
        allow_quickswap: bool = False
    ) -> Tuple[RandomizerResult, Dict[str, str]]:
        """
        Generate a mystery seed from mystery weights.

        Args:
            mystery_weights: Dictionary containing mystery weight configuration
            tournament: Whether this is a tournament seed
            spoilers: Spoiler level ('on', 'off', 'generate')
            allow_quickswap: Whether to allow quick swap

        Returns:
            Tuple of (RandomizerResult, rolled_settings_description)
            rolled_settings_description contains the rolled preset/settings info

        Raises:
            ValueError: If mystery weights are invalid
        """
        logger.info("Generating mystery seed from weights")

        # Roll the preset from weights
        rolled_settings, description = self._roll_mystery_settings(mystery_weights)

        # Generate the seed with rolled settings
        result = await self.alttpr_service.generate(
            settings_dict=rolled_settings,
            tournament=tournament,
            spoilers=spoilers,
            allow_quickswap=allow_quickswap
        )

        logger.info("Generated mystery seed with description: %s", description)

        return result, description

    def _roll_mystery_settings(self, mystery_weights: Dict[str, Any]) -> Tuple[Dict[str, Any], Dict[str, str]]:
        """
        Roll settings from mystery weights.

        Mystery generation workflow:
        1. Roll preset (if presets exist)
        2. Roll subweight (if exists)
        3. Roll entrance shuffle (if entrance_weights exist)
        4. Roll customizer settings (if customizer exists)

        Args:
            mystery_weights: Mystery weight configuration

        Returns:
            Tuple of (rolled_settings_dict, description_dict)
        """
        description = {}
        settings = {}

        # Step 1: Roll preset
        if 'weights' in mystery_weights:
            preset_name, preset_settings = self._roll_weighted_preset(mystery_weights['weights'])
            settings.update(preset_settings)
            description['preset'] = preset_name

            # Step 2: Roll subweight (if exists for this preset)
            if 'subweights' in mystery_weights and preset_name in mystery_weights['subweights']:
                subweight_name, subweight_settings = self._roll_weighted_preset(
                    mystery_weights['subweights'][preset_name]
                )
                settings.update(subweight_settings)
                description['subweight'] = subweight_name

        # Step 3: Roll entrance shuffle (if entrance_weights exist)
        if 'entrance_weights' in mystery_weights:
            entrance_value = self._roll_weighted_value(mystery_weights['entrance_weights'])
            if entrance_value and entrance_value != 'none':
                settings['entrance_shuffle'] = entrance_value
                description['entrance'] = entrance_value

        # Step 4: Roll customizer settings
        if 'customizer' in mystery_weights:
            customizer_settings = self._roll_customizer_settings(mystery_weights['customizer'])
            settings.update(customizer_settings)
            if customizer_settings:
                description['customizer'] = 'yes'

        return settings, description

    def _roll_weighted_preset(self, weights: Dict[str, Any]) -> Tuple[str, Dict[str, Any]]:
        """
        Roll a preset from weighted options.

        Args:
            weights: Dictionary of {preset_name: weight} or {preset_name: settings_dict}

        Returns:
            Tuple of (preset_name, settings_dict)
        """
        if not weights:
            return 'default', {}

        # Extract weights and settings
        preset_weights = {}
        preset_settings = {}

        for name, value in weights.items():
            if isinstance(value, dict):
                # Value is the settings dict with optional 'weight' key
                weight = value.pop('weight', 1) if 'weight' in value else 1
                preset_weights[name] = weight
                preset_settings[name] = value
            else:
                # Value is just the weight
                preset_weights[name] = value
                preset_settings[name] = {}

        # Roll based on weights
        selected_preset = self._weighted_random_choice(preset_weights)

        return selected_preset, preset_settings.get(selected_preset, {})

    def _roll_weighted_value(self, weights: Dict[str, float]) -> Optional[str]:
        """
        Roll a single value from weighted options.

        Args:
            weights: Dictionary of {value: weight}

        Returns:
            Selected value or None
        """
        if not weights:
            return None

        return self._weighted_random_choice(weights)

    def _roll_customizer_settings(self, customizer: Dict[str, Any]) -> Dict[str, Any]:
        """
        Roll customizer settings from mystery weights.

        Customizer supports:
        - eq (equipment settings)
        - custom (custom settings)
        - timed-ohko (timed OHKO settings)
        - triforce-hunt (triforce hunt settings)
        - pool sections (item pool modifications)

        Args:
            customizer: Customizer configuration

        Returns:
            Dictionary of rolled customizer settings
        """
        settings = {}

        for section, section_weights in customizer.items():
            if isinstance(section_weights, dict):
                # Roll settings for this section
                rolled_value = self._roll_weighted_value(section_weights)
                if rolled_value:
                    settings[section] = rolled_value

        return settings

    def _weighted_random_choice(self, weights: Dict[str, float]) -> str:
        """
        Make a weighted random choice from options.

        Args:
            weights: Dictionary of {option: weight}

        Returns:
            Selected option

        Raises:
            ValueError: If weights are empty or all weights are 0
        """
        if not weights:
            raise ValueError("Cannot choose from empty weights")

        options = list(weights.keys())
        weight_values = list(weights.values())

        # Ensure all weights are positive
        if all(w <= 0 for w in weight_values):
            raise ValueError("All weights are zero or negative")

        # Use random.choices for weighted selection
        selected = random.choices(options, weights=weight_values, k=1)[0]

        return selected

    async def generate_from_preset_name(
        self,
        mystery_preset_name: str,
        user_id: int,
        tournament: bool = True,
        spoilers: str = "off",
        allow_quickswap: bool = False
    ) -> Tuple[RandomizerResult, Dict[str, str]]:
        """
        Generate a mystery seed from a named mystery preset.

        Args:
            mystery_preset_name: Name of the mystery preset
            user_id: User ID requesting the preset
            tournament: Whether this is a tournament seed
            spoilers: Spoiler level
            allow_quickswap: Allow quickswap

        Returns:
            Tuple of (RandomizerResult, rolled_settings_description)

        Raises:
            ValueError: If preset is not found
            PermissionError: If user cannot access preset
        """
        from application.repositories.randomizer_preset_repository import RandomizerPresetRepository

        # Load mystery preset from database
        preset_repo = RandomizerPresetRepository()

        # Get preset by name
        preset = await preset_repo.get_by_name(
            randomizer='alttpr',
            name=mystery_preset_name
        )

        if not preset:
            raise ValueError(f"Mystery preset '{mystery_preset_name}' not found")

        # Check if user can access preset
        if not preset.is_public and preset.user_id != user_id:
            logger.warning(
                "User %s attempted to access private mystery preset %s owned by %s",
                user_id, mystery_preset_name, preset.user_id
            )
            raise PermissionError(f"Not authorized to access preset '{mystery_preset_name}'")

        # Check if this is a mystery preset
        preset_type = preset.settings.get('preset_type', 'standard')
        if preset_type != 'mystery':
            raise ValueError(f"Preset '{mystery_preset_name}' is not a mystery preset")

        # Extract mystery weights from preset
        mystery_weights = preset.settings.get('mystery_weights', {})
        if not mystery_weights:
            raise ValueError(f"Mystery preset '{mystery_preset_name}' has no mystery weights")

        # Generate mystery seed
        return await self.generate_from_mystery_weights(
            mystery_weights=mystery_weights,
            tournament=tournament,
            spoilers=spoilers,
            allow_quickswap=allow_quickswap
        )

    def validate_mystery_weights(self, mystery_weights: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """
        Validate mystery weight structure.

        Args:
            mystery_weights: Mystery weight configuration to validate

        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            # Check for required structure
            if not isinstance(mystery_weights, dict):
                return False, "Mystery weights must be a dictionary"

            # At least one of weights, entrance_weights, or customizer must exist
            if not any(key in mystery_weights for key in ['weights', 'entrance_weights', 'customizer']):
                return False, "Mystery weights must contain at least one of: weights, entrance_weights, customizer"

            # Validate weights structure
            if 'weights' in mystery_weights:
                weights = mystery_weights['weights']
                if not isinstance(weights, dict):
                    return False, "weights must be a dictionary"
                if not weights:
                    return False, "weights cannot be empty"

            # Validate subweights structure
            if 'subweights' in mystery_weights:
                subweights = mystery_weights['subweights']
                if not isinstance(subweights, dict):
                    return False, "subweights must be a dictionary"

            # Validate entrance_weights
            if 'entrance_weights' in mystery_weights:
                entrance_weights = mystery_weights['entrance_weights']
                if not isinstance(entrance_weights, dict):
                    return False, "entrance_weights must be a dictionary"

            # Validate customizer
            if 'customizer' in mystery_weights:
                customizer = mystery_weights['customizer']
                if not isinstance(customizer, dict):
                    return False, "customizer must be a dictionary"

            return True, None

        except Exception as e:
            return False, f"Validation error: {str(e)}"
