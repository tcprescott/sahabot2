"""
Preset repository.

This module provides data access methods for presets and preset namespaces.
"""

import logging
from typing import Optional, List
from models.preset import Preset, PresetNamespace
from models.user import User

logger = logging.getLogger(__name__)


class PresetRepository:
    """Repository for preset data access."""

    async def get_namespace_by_name(self, name: str) -> Optional[PresetNamespace]:
        """
        Get a namespace by name.

        Args:
            name: Namespace name

        Returns:
            PresetNamespace or None if not found
        """
        return await PresetNamespace.filter(name=name).first()

    async def get_namespace_by_id(self, namespace_id: int) -> Optional[PresetNamespace]:
        """
        Get a namespace by ID.

        Args:
            namespace_id: Namespace ID

        Returns:
            PresetNamespace or None if not found
        """
        return await PresetNamespace.filter(id=namespace_id).first()

    async def create_namespace(
        self,
        name: str,
        owner_discord_id: Optional[int] = None,
        is_public: bool = True,
        description: Optional[str] = None
    ) -> PresetNamespace:
        """
        Create a new namespace.

        Args:
            name: Namespace name
            owner_discord_id: Discord ID of the owner
            is_public: Whether the namespace is public
            description: Optional description

        Returns:
            Created PresetNamespace
        """
        namespace = await PresetNamespace.create(
            name=name,
            owner_discord_id=owner_discord_id,
            is_public=is_public,
            description=description
        )
        logger.info("Created namespace %s", name)
        return namespace

    async def get_or_create_namespace(
        self,
        name: str,
        owner_discord_id: Optional[int] = None
    ) -> PresetNamespace:
        """
        Get or create a namespace.

        Args:
            name: Namespace name
            owner_discord_id: Discord ID of the owner

        Returns:
            PresetNamespace (existing or newly created)
        """
        namespace = await self.get_namespace_by_name(name)
        if namespace:
            return namespace

        return await self.create_namespace(name, owner_discord_id)

    async def list_namespaces(self, public_only: bool = False) -> List[PresetNamespace]:
        """
        List all namespaces.

        Args:
            public_only: If True, only return public namespaces

        Returns:
            List of PresetNamespace
        """
        query = PresetNamespace.all()
        if public_only:
            query = query.filter(is_public=True)

        return await query.order_by('name')

    async def add_collaborator(self, namespace: PresetNamespace, user: User) -> None:
        """
        Add a collaborator to a namespace.

        Args:
            namespace: PresetNamespace instance
            user: User to add as collaborator
        """
        await namespace.collaborators.add(user)
        logger.info("Added user %s as collaborator to namespace %s", user.id, namespace.name)

    async def remove_collaborator(self, namespace: PresetNamespace, user: User) -> None:
        """
        Remove a collaborator from a namespace.

        Args:
            namespace: PresetNamespace instance
            user: User to remove
        """
        await namespace.collaborators.remove(user)
        logger.info("Removed user %s from namespace %s", user.id, namespace.name)

    async def get_preset(
        self,
        namespace_name: str,
        preset_name: str,
        randomizer: str
    ) -> Optional[Preset]:
        """
        Get a specific preset.

        Args:
            namespace_name: Namespace name
            preset_name: Preset name
            randomizer: Randomizer type

        Returns:
            Preset or None if not found
        """
        return await Preset.filter(
            namespace__name=namespace_name,
            preset_name=preset_name,
            randomizer=randomizer
        ).prefetch_related('namespace').first()

    async def get_preset_by_id(self, preset_id: int) -> Optional[Preset]:
        """
        Get a preset by ID.

        Args:
            preset_id: Preset ID

        Returns:
            Preset or None if not found
        """
        return await Preset.filter(id=preset_id).prefetch_related('namespace').first()

    async def list_presets(
        self,
        namespace_name: Optional[str] = None,
        randomizer: Optional[str] = None
    ) -> List[Preset]:
        """
        List presets with optional filters.

        Args:
            namespace_name: Filter by namespace name
            randomizer: Filter by randomizer type

        Returns:
            List of Preset
        """
        query = Preset.all().prefetch_related('namespace')

        if namespace_name:
            query = query.filter(namespace__name=namespace_name)

        if randomizer:
            query = query.filter(randomizer=randomizer)

        return await query.order_by('namespace__name', 'preset_name')

    async def create_preset(
        self,
        namespace: PresetNamespace,
        preset_name: str,
        randomizer: str,
        content: str,
        description: Optional[str] = None
    ) -> Preset:
        """
        Create a new preset.

        Args:
            namespace: PresetNamespace instance
            preset_name: Preset name
            randomizer: Randomizer type
            content: Preset content (YAML)
            description: Optional description

        Returns:
            Created Preset
        """
        preset = await Preset.create(
            namespace=namespace,
            preset_name=preset_name,
            randomizer=randomizer,
            content=content,
            description=description
        )
        logger.info("Created preset %s/%s (%s)", namespace.name, preset_name, randomizer)
        return preset

    async def update_preset(
        self,
        preset: Preset,
        content: Optional[str] = None,
        description: Optional[str] = None
    ) -> Preset:
        """
        Update a preset.

        Args:
            preset: Preset instance to update
            content: New content (if provided)
            description: New description (if provided)

        Returns:
            Updated Preset
        """
        if content is not None:
            preset.content = content

        if description is not None:
            preset.description = description

        await preset.save()
        logger.info("Updated preset %s", preset.id)
        return preset

    async def delete_preset(self, preset: Preset) -> None:
        """
        Delete a preset.

        Args:
            preset: Preset instance to delete
        """
        preset_id = preset.id
        await preset.delete()
        logger.info("Deleted preset %s", preset_id)

    async def update_or_create_preset(
        self,
        namespace: PresetNamespace,
        preset_name: str,
        randomizer: str,
        content: str,
        description: Optional[str] = None
    ) -> Preset:
        """
        Update an existing preset or create a new one.

        Args:
            namespace: PresetNamespace instance
            preset_name: Preset name
            randomizer: Randomizer type
            content: Preset content (YAML)
            description: Optional description

        Returns:
            Preset (existing or newly created)
        """
        preset = await self.get_preset(namespace.name, preset_name, randomizer)

        if preset:
            return await self.update_preset(preset, content=content, description=description)
        else:
            return await self.create_preset(namespace, preset_name, randomizer, content, description)
