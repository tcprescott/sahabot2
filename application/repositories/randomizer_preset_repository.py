"""
Randomizer preset repository for data access.

This module handles all database operations for randomizer presets.
"""

import logging
from typing import Optional
from tortoise.expressions import Q
from models.randomizer_preset import RandomizerPreset
from models.preset_namespace import PresetNamespace

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
        return await RandomizerPreset.get_or_none(id=preset_id).prefetch_related(
            "user", "namespace"
        )

    async def get_by_name(
        self, randomizer: str, name: str, namespace_id: Optional[int] = None
    ) -> Optional[RandomizerPreset]:
        """
        Get a preset by randomizer and name.

        Args:
            randomizer: Randomizer type
            name: Preset name
            namespace_id: Optional namespace ID (None for global presets)

        Returns:
            RandomizerPreset if found, None otherwise
        """
        return await RandomizerPreset.get_or_none(
            namespace_id=namespace_id, randomizer=randomizer, name=name
        ).prefetch_related("user", "namespace")

    async def get_global_preset(
        self, randomizer: str, name: str
    ) -> Optional[RandomizerPreset]:
        """
        Get a global preset by randomizer and name.

        Args:
            randomizer: Randomizer type
            name: Preset name

        Returns:
            RandomizerPreset if found, None otherwise
        """
        return await RandomizerPreset.get_or_none(
            namespace_id=None, randomizer=randomizer, name=name
        ).prefetch_related("user", "namespace")

    async def list_global_presets(
        self, randomizer: Optional[str] = None
    ) -> list[RandomizerPreset]:
        """
        List global (non-namespaced) presets.

        Args:
            randomizer: Optional filter by randomizer type

        Returns:
            List of global presets
        """
        query = RandomizerPreset.filter(namespace_id=None)

        if randomizer:
            query = query.filter(randomizer=randomizer)

        return await query.prefetch_related("user", "namespace").order_by("-updated_at")

    async def list_in_namespace(
        self, namespace_id: int, randomizer: Optional[str] = None
    ) -> list[RandomizerPreset]:
        """
        List presets in a specific namespace.

        Args:
            namespace_id: Namespace ID
            randomizer: Optional filter by randomizer type

        Returns:
            List of presets in the namespace
        """
        query = RandomizerPreset.filter(namespace_id=namespace_id)

        if randomizer:
            query = query.filter(randomizer=randomizer)

        return await query.prefetch_related("user", "namespace").order_by("-updated_at")

    async def list_presets(
        self,
        randomizer: Optional[str] = None,
        user_id: Optional[int] = None,
        include_public: bool = True,
    ) -> list[RandomizerPreset]:
        """
        List presets globally (legacy method for backward compatibility).

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

        return await query.prefetch_related("user", "namespace").order_by("-updated_at")

    async def list_accessible_presets(
        self,
        namespaces: list[PresetNamespace],
        randomizer: Optional[str] = None,
        include_global: bool = True,
        user_id: Optional[int] = None,
    ) -> list[RandomizerPreset]:
        """
        List presets accessible through given namespaces.

        Shows all presets from user's own namespaces, but only public presets
        from other namespaces.

        Args:
            namespaces: List of accessible namespaces
            randomizer: Optional filter by randomizer type
            include_global: Whether to include global presets
            user_id: Optional user ID to determine which are user's own namespaces

        Returns:
            List of presets from the given namespaces plus global presets
        """
        presets = []

        # Get global presets if requested
        if include_global:
            global_presets = await self.list_global_presets(randomizer)
            presets.extend(global_presets)

        # Get namespace presets
        if namespaces:
            # Separate user's own namespaces from others
            user_namespace_ids = []
            other_namespace_ids = []

            for ns in namespaces:
                if user_id and ns.user_id == user_id:
                    user_namespace_ids.append(ns.id)
                else:
                    other_namespace_ids.append(ns.id)

            # Get all presets from user's own namespaces
            if user_namespace_ids:
                query = RandomizerPreset.filter(namespace_id__in=user_namespace_ids)
                if randomizer:
                    query = query.filter(randomizer=randomizer)
                user_presets = await query.prefetch_related(
                    "user", "namespace"
                ).order_by("-updated_at")
                presets.extend(user_presets)

            # Get only public presets from other namespaces
            if other_namespace_ids:
                query = RandomizerPreset.filter(
                    namespace_id__in=other_namespace_ids, is_public=True
                )
                if randomizer:
                    query = query.filter(randomizer=randomizer)
                public_presets = await query.prefetch_related(
                    "user", "namespace"
                ).order_by("-updated_at")
                presets.extend(public_presets)

        return presets

    async def create(
        self,
        user_id: int,
        randomizer: str,
        name: str,
        settings: dict,
        namespace_id: Optional[int] = None,
        description: Optional[str] = None,
        is_public: bool = False,
    ) -> RandomizerPreset:
        """
        Create a new preset.

        Args:
            user_id: User ID creating the preset
            randomizer: Randomizer type
            name: Preset name
            settings: Preset settings (YAML as dict)
            namespace_id: Optional namespace ID (None for global presets)
            description: Optional description
            is_public: Whether preset is public

        Returns:
            Created RandomizerPreset
        """
        preset = await RandomizerPreset.create(
            namespace_id=namespace_id,
            user_id=user_id,
            randomizer=randomizer,
            name=name,
            settings=settings,
            description=description,
            is_public=is_public,
        )
        await preset.fetch_related("user", "namespace")

        scope = "global" if namespace_id is None else f"namespace {namespace_id}"
        logger.info(
            "Created preset %s/%s in %s by user %s", randomizer, name, scope, user_id
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
        allowed_fields = {"name", "description", "settings", "is_public"}
        update_fields = {k: v for k, v in fields.items() if k in allowed_fields}

        if update_fields:
            await preset.update_from_dict(update_fields)
            await preset.save()
            logger.info(
                "Updated preset %s (id=%s) fields: %s",
                preset.full_name,
                preset_id,
                list(update_fields.keys()),
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
