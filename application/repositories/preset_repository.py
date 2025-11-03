"""
Repository for randomizer preset data access.

This module provides data access methods for RandomizerPreset model.
"""

import logging
from typing import Optional, List
from models.randomizer_preset import RandomizerPreset
from models.organizations import Organization

logger = logging.getLogger(__name__)


class PresetRepository:
    """
    Repository for randomizer preset data access.

    Handles all database operations for RandomizerPreset model,
    enforcing organization-based (tenant) isolation.
    """

    async def get_by_id(
        self,
        preset_id: int,
        organization_id: int
    ) -> Optional[RandomizerPreset]:
        """
        Get a preset by ID within an organization.

        Args:
            preset_id: Preset ID
            organization_id: Organization ID for tenant isolation

        Returns:
            RandomizerPreset if found, None otherwise
        """
        return await RandomizerPreset.filter(
            id=preset_id,
            organization_id=organization_id
        ).first()

    async def get_by_name(
        self,
        name: str,
        organization_id: int
    ) -> Optional[RandomizerPreset]:
        """
        Get a preset by name within an organization.

        Args:
            name: Preset name
            organization_id: Organization ID for tenant isolation

        Returns:
            RandomizerPreset if found, None otherwise
        """
        return await RandomizerPreset.filter(
            name=name,
            organization_id=organization_id,
            is_active=True
        ).first()

    async def list_by_organization(
        self,
        organization_id: int,
        randomizer: Optional[str] = None,
        active_only: bool = True
    ) -> List[RandomizerPreset]:
        """
        List all presets for an organization.

        Args:
            organization_id: Organization ID for tenant isolation
            randomizer: Optional filter by randomizer type
            active_only: Whether to return only active presets

        Returns:
            List of RandomizerPreset objects
        """
        query = RandomizerPreset.filter(organization_id=organization_id)

        if randomizer:
            query = query.filter(randomizer=randomizer)

        if active_only:
            query = query.filter(is_active=True)

        return await query.all()

    async def create(
        self,
        organization_id: int,
        name: str,
        randomizer: str,
        settings: dict,
        description: Optional[str] = None
    ) -> RandomizerPreset:
        """
        Create a new preset.

        Args:
            organization_id: Organization ID for tenant isolation
            name: Preset name
            randomizer: Randomizer type
            settings: Preset settings dictionary
            description: Optional description

        Returns:
            Created RandomizerPreset

        Raises:
            IntegrityError: If preset with same name already exists in organization
        """
        preset = await RandomizerPreset.create(
            organization_id=organization_id,
            name=name,
            randomizer=randomizer,
            settings=settings,
            description=description
        )
        logger.info(
            "Created preset %s for organization %s",
            preset.name,
            organization_id
        )
        return preset

    async def update(
        self,
        preset_id: int,
        organization_id: int,
        **kwargs
    ) -> Optional[RandomizerPreset]:
        """
        Update a preset.

        Args:
            preset_id: Preset ID
            organization_id: Organization ID for tenant isolation
            **kwargs: Fields to update

        Returns:
            Updated RandomizerPreset if found, None otherwise
        """
        preset = await self.get_by_id(preset_id, organization_id)
        if not preset:
            return None

        for key, value in kwargs.items():
            if hasattr(preset, key):
                setattr(preset, key, value)

        await preset.save()
        logger.info(
            "Updated preset %s (id=%s) for organization %s",
            preset.name,
            preset_id,
            organization_id
        )
        return preset

    async def delete(
        self,
        preset_id: int,
        organization_id: int
    ) -> bool:
        """
        Delete a preset (soft delete by setting is_active=False).

        Args:
            preset_id: Preset ID
            organization_id: Organization ID for tenant isolation

        Returns:
            True if deleted, False if not found
        """
        preset = await self.get_by_id(preset_id, organization_id)
        if not preset:
            return False

        preset.is_active = False
        await preset.save()
        logger.info(
            "Deleted preset %s (id=%s) for organization %s",
            preset.name,
            preset_id,
            organization_id
        )
        return True
