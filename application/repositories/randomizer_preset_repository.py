"""
Randomizer preset repository for data access.

This module handles all database operations for randomizer presets.
"""

import logging
from typing import Optional
from tortoise.expressions import Q
from models.randomizer_preset import RandomizerPreset

logger = logging.getLogger(__name__)


class RandomizerPresetRepository:
    """Repository for randomizer preset data access operations."""

    async def get_by_id(self, preset_id: int) -> Optional[RandomizerPreset]:
        """
        Get a preset by ID.

        Args:
            preset_id: Preset ID

        Returns:
            RandomizerPreset if found, None otherwise
        """
        return await RandomizerPreset.get_or_none(id=preset_id).prefetch_related('user')

    async def get_by_name(self, randomizer: str, name: str) -> Optional[RandomizerPreset]:
        """
        Get a preset by name and randomizer.

        Args:
            randomizer: Randomizer type
            name: Preset name

        Returns:
            RandomizerPreset if found, None otherwise
        """
        return await RandomizerPreset.get_or_none(
            randomizer=randomizer,
            name=name
        ).prefetch_related('user')

    async def list_presets(
        self,
        randomizer: Optional[str] = None,
        user_id: Optional[int] = None,
        include_public: bool = True
    ) -> list[RandomizerPreset]:
        """
        List presets globally.

        Args:
            randomizer: Optional filter by randomizer type
            user_id: Optional filter by user (shows user's presets + public)
            include_public: Whether to include public presets

        Returns:
            List of presets
        """
        query = RandomizerPreset.all()

        if randomizer:
            query = query.filter(randomizer=randomizer)

        if user_id is not None:
            # Show user's own presets OR public presets
            if include_public:
                query = query.filter(Q(user_id=user_id) | Q(is_public=True))
            else:
                query = query.filter(user_id=user_id)
        elif include_public:
            query = query.filter(is_public=True)

        return await query.prefetch_related('user').order_by('-updated_at')

    async def create(
        self,
        user_id: int,
        randomizer: str,
        name: str,
        settings: dict,
        description: Optional[str] = None,
        is_public: bool = False
    ) -> RandomizerPreset:
        """
        Create a new preset.

        Args:
            user_id: User ID creating the preset
            randomizer: Randomizer type
            name: Preset name
            settings: Preset settings (YAML as dict)
            description: Optional description
            is_public: Whether preset is public

        Returns:
            Created RandomizerPreset
        """
        preset = await RandomizerPreset.create(
            user_id=user_id,
            randomizer=randomizer,
            name=name,
            settings=settings,
            description=description,
            is_public=is_public
        )
        await preset.fetch_related('user')
        logger.info(
            "Created preset %s/%s by user %s",
            randomizer,
            name,
            user_id
        )
        return preset

    async def update(self, preset_id: int, **fields) -> Optional[RandomizerPreset]:
        """
        Update a preset.

        Args:
            preset_id: Preset ID
            **fields: Fields to update

        Returns:
            Updated RandomizerPreset if found and updated, None otherwise
        """
        preset = await self.get_by_id(preset_id)
        if not preset:
            return None

        # Only allow updating specific fields
        allowed_fields = {'name', 'description', 'settings', 'is_public'}
        update_fields = {k: v for k, v in fields.items() if k in allowed_fields}

        if update_fields:
            await preset.update_from_dict(update_fields)
            await preset.save()
            logger.info(
                "Updated preset %s (id=%s) fields: %s",
                preset.full_name,
                preset_id,
                list(update_fields.keys())
            )

        return preset

    async def delete(self, preset_id: int) -> bool:
        """
        Delete a preset.

        Args:
            preset_id: Preset ID

        Returns:
            True if deleted, False if not found
        """
        preset = await self.get_by_id(preset_id)
        if not preset:
            return False

        logger.info("Deleting preset %s (id=%s)", preset.full_name, preset_id)
        await preset.delete()
        return True

    async def count_presets(self, randomizer: Optional[str] = None) -> int:
        """
        Count presets globally.

        Args:
            randomizer: Optional filter by randomizer type

        Returns:
            Number of presets
        """
        query = RandomizerPreset.all()
        if randomizer:
            query = query.filter(randomizer=randomizer)
        return await query.count()
