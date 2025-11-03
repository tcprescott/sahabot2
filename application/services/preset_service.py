"""
Service for managing randomizer presets.

This module provides business logic for randomizer preset operations.
"""

import logging
from typing import Optional, List, Dict, Any
from application.repositories.preset_repository import PresetRepository
from models.randomizer_preset import RandomizerPreset

logger = logging.getLogger(__name__)


class PresetService:
    """
    Service for managing randomizer presets.

    Handles business logic for preset operations, including
    validation and organization-scoped access control.
    """

    def __init__(self):
        """Initialize the preset service."""
        self.repository = PresetRepository()

    async def get_preset(
        self,
        preset_id: int,
        organization_id: int
    ) -> Optional[RandomizerPreset]:
        """
        Get a preset by ID.

        Args:
            preset_id: Preset ID
            organization_id: Organization ID for tenant isolation

        Returns:
            RandomizerPreset if found and accessible, None otherwise
        """
        return await self.repository.get_by_id(preset_id, organization_id)

    async def get_preset_by_name(
        self,
        name: str,
        organization_id: int
    ) -> Optional[RandomizerPreset]:
        """
        Get a preset by name.

        Args:
            name: Preset name
            organization_id: Organization ID for tenant isolation

        Returns:
            RandomizerPreset if found and accessible, None otherwise
        """
        return await self.repository.get_by_name(name, organization_id)

    async def list_presets(
        self,
        organization_id: int,
        randomizer: Optional[str] = None,
        active_only: bool = True
    ) -> List[RandomizerPreset]:
        """
        List presets for an organization.

        Args:
            organization_id: Organization ID for tenant isolation
            randomizer: Optional filter by randomizer type
            active_only: Whether to return only active presets

        Returns:
            List of RandomizerPreset objects
        """
        return await self.repository.list_by_organization(
            organization_id,
            randomizer=randomizer,
            active_only=active_only
        )

    async def create_preset(
        self,
        organization_id: int,
        name: str,
        randomizer: str,
        settings: Dict[str, Any],
        description: Optional[str] = None
    ) -> RandomizerPreset:
        """
        Create a new preset.

        Args:
            organization_id: Organization ID for tenant isolation
            name: Preset name (must be unique within organization)
            randomizer: Randomizer type (alttpr, sm, smz3, etc.)
            settings: Preset settings dictionary
            description: Optional description

        Returns:
            Created RandomizerPreset

        Raises:
            ValueError: If preset name already exists or validation fails
        """
        # Validate randomizer type
        valid_randomizers = [
            'alttpr', 'aosr', 'z1r', 'ootr', 'ffr',
            'smb3r', 'sm', 'smz3', 'ctjets', 'bingosync'
        ]
        if randomizer not in valid_randomizers:
            raise ValueError(
                f"Invalid randomizer type: {randomizer}. "
                f"Must be one of: {', '.join(valid_randomizers)}"
            )

        # Check for duplicate name
        existing = await self.repository.get_by_name(name, organization_id)
        if existing:
            raise ValueError(
                f"Preset with name '{name}' already exists in this organization"
            )

        # Validate settings is a dict
        if not isinstance(settings, dict):
            raise ValueError("Settings must be a dictionary")

        return await self.repository.create(
            organization_id=organization_id,
            name=name,
            randomizer=randomizer,
            settings=settings,
            description=description
        )

    async def update_preset(
        self,
        preset_id: int,
        organization_id: int,
        name: Optional[str] = None,
        settings: Optional[Dict[str, Any]] = None,
        description: Optional[str] = None,
        is_active: Optional[bool] = None
    ) -> Optional[RandomizerPreset]:
        """
        Update a preset.

        Args:
            preset_id: Preset ID
            organization_id: Organization ID for tenant isolation
            name: Optional new name
            settings: Optional new settings
            description: Optional new description
            is_active: Optional active status

        Returns:
            Updated RandomizerPreset if found, None otherwise

        Raises:
            ValueError: If validation fails
        """
        # Build update dict
        updates = {}
        if name is not None:
            # Check for duplicate name
            existing = await self.repository.get_by_name(name, organization_id)
            if existing and existing.id != preset_id:
                raise ValueError(
                    f"Preset with name '{name}' already exists in this organization"
                )
            updates['name'] = name
        if settings is not None:
            if not isinstance(settings, dict):
                raise ValueError("Settings must be a dictionary")
            updates['settings'] = settings
        if description is not None:
            updates['description'] = description
        if is_active is not None:
            updates['is_active'] = is_active

        if not updates:
            # Nothing to update, just return the existing preset
            return await self.repository.get_by_id(preset_id, organization_id)

        return await self.repository.update(
            preset_id,
            organization_id,
            **updates
        )

    async def delete_preset(
        self,
        preset_id: int,
        organization_id: int
    ) -> bool:
        """
        Delete a preset (soft delete).

        Args:
            preset_id: Preset ID
            organization_id: Organization ID for tenant isolation

        Returns:
            True if deleted, False if not found
        """
        return await self.repository.delete(preset_id, organization_id)

    async def get_preset_settings(
        self,
        preset_name: str,
        organization_id: int
    ) -> Optional[Dict[str, Any]]:
        """
        Get the settings dictionary for a preset by name.

        This is a convenience method for use by randomizer services.

        Args:
            preset_name: Preset name
            organization_id: Organization ID for tenant isolation

        Returns:
            Settings dictionary if preset found, None otherwise
        """
        preset = await self.get_preset_by_name(preset_name, organization_id)
        if preset:
            logger.info(
                "Retrieved settings for preset %s in organization %s",
                preset_name,
                organization_id
            )
            return preset.settings
        else:
            logger.warning(
                "Preset %s not found in organization %s",
                preset_name,
                organization_id
            )
            return None
