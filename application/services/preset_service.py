"""
Preset service.

This module provides business logic for preset management.
"""

import logging
import yaml
from typing import Optional, List, Dict, Any
from application.repositories.preset_repository import PresetRepository
from models.preset import Preset, PresetNamespace
from models.user import User

logger = logging.getLogger(__name__)


class PresetService:
    """Service for preset business logic."""

    def __init__(self):
        """Initialize preset service."""
        self.repository = PresetRepository()

    async def get_namespace(self, name: str) -> Optional[PresetNamespace]:
        """
        Get a namespace by name.

        Args:
            name: Namespace name

        Returns:
            PresetNamespace or None if not found
        """
        return await self.repository.get_namespace_by_name(name)

    async def create_namespace(
        self,
        name: str,
        owner: Optional[User] = None,
        is_public: bool = True,
        description: Optional[str] = None
    ) -> PresetNamespace:
        """
        Create a new namespace.

        Args:
            name: Namespace name
            owner: Owner user (optional)
            is_public: Whether the namespace is public
            description: Optional description

        Returns:
            Created PresetNamespace
        """
        owner_discord_id = owner.discord_id if owner else None
        return await self.repository.create_namespace(
            name, owner_discord_id, is_public, description
        )

    async def get_or_create_namespace(
        self,
        name: str,
        owner: Optional[User] = None
    ) -> PresetNamespace:
        """
        Get or create a namespace for a user.

        Args:
            name: Namespace name
            owner: Owner user (optional)

        Returns:
            PresetNamespace (existing or newly created)
        """
        owner_discord_id = owner.discord_id if owner else None
        return await self.repository.get_or_create_namespace(name, owner_discord_id)

    async def list_namespaces(
        self,
        public_only: bool = False,
        user: Optional[User] = None
    ) -> List[PresetNamespace]:
        """
        List namespaces accessible to a user.

        Args:
            public_only: If True, only return public namespaces
            user: User making the request (optional)

        Returns:
            List of PresetNamespace
        """
        namespaces = await self.repository.list_namespaces(public_only)

        # If user is provided, also fetch their private namespaces
        if user and not public_only:
            # Filter to show public namespaces + user's own namespaces
            return [
                ns for ns in namespaces
                if ns.is_public or (ns.owner_discord_id == user.discord_id)
            ]

        return namespaces

    def is_namespace_owner(self, user: Optional[User], namespace: PresetNamespace) -> bool:
        """
        Check if a user is the owner of a namespace.

        Args:
            user: User to check
            namespace: PresetNamespace to check

        Returns:
            True if user is the owner, False otherwise
        """
        if not user:
            return False

        return namespace.owner_discord_id == user.discord_id

    async def can_edit_namespace(
        self,
        user: Optional[User],
        namespace: PresetNamespace
    ) -> bool:
        """
        Check if a user can edit a namespace.

        Args:
            user: User to check
            namespace: PresetNamespace to check

        Returns:
            True if user can edit, False otherwise
        """
        if not user:
            return False

        # Owner can edit
        if self.is_namespace_owner(user, namespace):
            return True

        # Check if user is a collaborator
        await namespace.fetch_related('collaborators')
        return await namespace.collaborators.filter(id=user.id).exists()

    async def add_collaborator(
        self,
        namespace: PresetNamespace,
        user: User,
        current_user: User
    ) -> bool:
        """
        Add a collaborator to a namespace.

        Args:
            namespace: PresetNamespace instance
            user: User to add as collaborator
            current_user: User making the request

        Returns:
            True if successful, False otherwise
        """
        # Only owner can add collaborators
        if not self.is_namespace_owner(current_user, namespace):
            logger.warning("User %s attempted to add collaborator to namespace %s without permission",
                          current_user.id, namespace.name)
            return False

        await self.repository.add_collaborator(namespace, user)
        return True

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
        return await self.repository.get_preset(namespace_name, preset_name, randomizer)

    async def list_presets(
        self,
        namespace_name: Optional[str] = None,
        randomizer: Optional[str] = None,
        user: Optional[User] = None
    ) -> List[Preset]:
        """
        List presets accessible to a user.

        Args:
            namespace_name: Filter by namespace name
            randomizer: Filter by randomizer type
            user: User making the request (optional)

        Returns:
            List of Preset
        """
        presets = await self.repository.list_presets(namespace_name, randomizer)

        # Filter by namespace visibility
        if user:
            # Show presets from public namespaces or user's own namespaces
            return [
                preset for preset in presets
                if preset.namespace.is_public or
                (preset.namespace.owner_discord_id == user.discord_id)
            ]
        else:
            # Only show presets from public namespaces
            return [preset for preset in presets if preset.namespace.is_public]

    async def create_preset(
        self,
        namespace_name: str,
        preset_name: str,
        randomizer: str,
        content: str,
        user: Optional[User] = None,
        description: Optional[str] = None
    ) -> Optional[Preset]:
        """
        Create a new preset.

        Args:
            namespace_name: Namespace name
            preset_name: Preset name
            randomizer: Randomizer type
            content: Preset content (YAML)
            user: User creating the preset
            description: Optional description

        Returns:
            Created Preset or None if unauthorized
        """
        # Get or create namespace
        namespace = await self.get_or_create_namespace(namespace_name, user)

        # Check permissions
        if not await self.can_edit_namespace(user, namespace):
            logger.warning("User %s attempted to create preset in namespace %s without permission",
                          user.id if user else None, namespace_name)
            return None

        # Validate YAML
        try:
            yaml.safe_load(content)
        except yaml.YAMLError as e:
            logger.error("Invalid YAML content for preset %s/%s: %s", namespace_name, preset_name, e)
            raise ValueError(f"Invalid YAML content: {e}")

        return await self.repository.create_preset(
            namespace, preset_name, randomizer, content, description
        )

    async def update_preset(
        self,
        preset: Preset,
        content: Optional[str] = None,
        description: Optional[str] = None,
        user: Optional[User] = None
    ) -> bool:
        """
        Update a preset.

        Args:
            preset: Preset to update
            content: New content (if provided)
            description: New description (if provided)
            user: User making the update

        Returns:
            True if successful, False otherwise
        """
        # Check permissions
        await preset.fetch_related('namespace')
        if not await self.can_edit_namespace(user, preset.namespace):
            logger.warning("User %s attempted to update preset %s without permission",
                          user.id if user else None, preset.id)
            return False

        # Validate YAML if content is provided
        if content:
            try:
                yaml.safe_load(content)
            except yaml.YAMLError as e:
                logger.error("Invalid YAML content for preset %s: %s", preset.id, e)
                raise ValueError(f"Invalid YAML content: {e}")

        await self.repository.update_preset(preset, content, description)
        return True

    async def delete_preset(
        self,
        preset: Preset,
        user: Optional[User] = None
    ) -> bool:
        """
        Delete a preset.

        Args:
            preset: Preset to delete
            user: User making the deletion

        Returns:
            True if successful, False otherwise
        """
        # Check permissions
        await preset.fetch_related('namespace')
        if not await self.can_edit_namespace(user, preset.namespace):
            logger.warning("User %s attempted to delete preset %s without permission",
                          user.id if user else None, preset.id)
            return False

        await self.repository.delete_preset(preset)
        return True

    async def get_preset_content_as_dict(self, preset: Preset) -> Dict[str, Any]:
        """
        Parse preset content as a dictionary.

        Args:
            preset: Preset to parse

        Returns:
            Dictionary with preset settings

        Raises:
            ValueError: If YAML is invalid
        """
        try:
            return yaml.safe_load(preset.content)
        except yaml.YAMLError as e:
            logger.error("Failed to parse YAML for preset %s: %s", preset.id, e)
            raise ValueError(f"Invalid YAML content: {e}")

    async def list_presets_for_randomizer(
        self,
        randomizer: str,
        include_namespace_names: bool = False
    ) -> List[str] | Dict[str, List[str]]:
        """
        Get a list of preset names for a specific randomizer.

        This is useful for displaying available presets to users.

        Args:
            randomizer: Randomizer type
            include_namespace_names: If True, return dict with namespace -> [presets]

        Returns:
            List of preset names or dict of namespace -> preset names
        """
        presets = await self.repository.list_presets(randomizer=randomizer)

        if include_namespace_names:
            # Group by namespace
            result = {}
            for preset in presets:
                ns_name = preset.namespace.name
                if ns_name not in result:
                    result[ns_name] = []
                result[ns_name].append(preset.preset_name)
            return result
        else:
            # Return flat list with namespace prefix
            return [f"{preset.namespace.name}/{preset.preset_name}" for preset in presets]
