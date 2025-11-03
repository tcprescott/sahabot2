"""
Randomizer preset service for business logic.

This module handles business logic for managing randomizer presets,
including authorization, validation, YAML parsing, and namespace management.
"""

import logging
import yaml
from typing import Optional
from models import User, RandomizerPreset, Permission
from application.repositories.randomizer_preset_repository import RandomizerPresetRepository
from application.services.preset_namespace_service import PresetNamespaceService

logger = logging.getLogger(__name__)


class PresetValidationError(Exception):
    """Exception raised when preset validation fails."""


class RandomizerPresetService:
    """Service for managing randomizer presets with namespace support."""

    SUPPORTED_RANDOMIZERS = [
        'alttpr',
        'sm',
        'smz3',
        'ootr',
        'aosr',
        'z1r',
        'ffr',
        'smb3r',
        'ctjets',
        'bingosync'
    ]

    def __init__(self):
        """Initialize the preset service."""
        self.repository = RandomizerPresetRepository()
        self.namespace_service = PresetNamespaceService()

    def _can_edit_preset(self, preset: RandomizerPreset, user: User) -> bool:
        """
        Check if user can edit a preset.

        Users can edit their own presets or if they're a SUPERADMIN.
        """
        # Owner can always edit
        if preset.user_id == user.id:
            return True

        # SUPERADMIN can edit anything
        return user.has_permission(Permission.SUPERADMIN)

    def _can_view_preset(self, preset: RandomizerPreset, user: Optional[User]) -> bool:
        """
        Check if user can view a preset.

        Public presets are visible to everyone.
        Private presets only to owners.
        """
        if preset.is_public:
            return True

        if user and preset.user_id == user.id:
            return True

        return False

    async def can_user_edit_preset(self, preset_id: int, user: User) -> bool:
        """
        Check if user can edit a preset (public API).

        Args:
            preset_id: Preset ID
            user: User to check

        Returns:
            True if user can edit the preset
        """
        preset = await self.repository.get_by_id(preset_id)
        if not preset:
            return False

        return self._can_edit_preset(preset, user)

    async def get_preset(
        self,
        preset_id: int,
        user: Optional[User] = None
    ) -> Optional[RandomizerPreset]:
        """
        Get a preset by ID.

        Authorization: Anyone can view public presets, users can view their own.

        Args:
            preset_id: Preset ID
            user: Optional user for authorization

        Returns:
            RandomizerPreset if found and authorized, None otherwise
        """
        preset = await self.repository.get_by_id(preset_id)
        if not preset:
            return None

        if not self._can_view_preset(preset, user):
            logger.warning(
                "User %s attempted to access private preset %s",
                user.id if user else None,
                preset_id
            )
            return None

        return preset

    async def list_presets(
        self,
        user: Optional[User] = None,
        randomizer: Optional[str] = None,
        mine_only: bool = False,
        include_global: bool = True
    ) -> list[RandomizerPreset]:
        """
        List presets accessible to a user through their namespaces.

        Args:
            user: Optional user (to show their accessible presets)
            randomizer: Optional filter by randomizer type
            mine_only: Only show user's own presets (from their namespace)
            include_global: Whether to include global presets

        Returns:
            List of presets user can access
        """
        if not user:
            # No user - show only global public presets (legacy behavior)
            if include_global:
                return await self.repository.list_global_presets(randomizer=randomizer)
            return []

        if mine_only:
            # Get user's namespace
            namespace = await self.namespace_service.get_or_create_user_namespace(user)
            if not namespace:
                return []
            presets = await self.repository.list_in_namespace(
                namespace_id=namespace.id,
                randomizer=randomizer
            )
            # Optionally include global presets
            if include_global:
                global_presets = await self.repository.list_global_presets(randomizer=randomizer)
                presets.extend(global_presets)
            return presets

        # Get all accessible namespaces
        namespaces = await self.namespace_service.list_accessible_namespaces(user)
        return await self.repository.list_accessible_presets(
            namespaces=namespaces,
            randomizer=randomizer,
            include_global=include_global
        )

    async def create_preset(
        self,
        user: User,
        randomizer: str,
        name: str,
        yaml_content: str,
        description: Optional[str] = None,
        is_public: bool = False,
        is_global: bool = False
    ) -> RandomizerPreset:
        """
        Create a new preset in the user's namespace or as a global preset.

        If the user doesn't have a namespace, one will be created automatically
        (unless creating a global preset).

        Args:
            user: User creating the preset
            randomizer: Randomizer type
            name: Preset name
            yaml_content: YAML content as string
            description: Optional description
            is_public: Whether preset is publicly visible
            is_global: Whether to create as a global preset (requires SUPERADMIN)

        Returns:
            Created RandomizerPreset

        Raises:
            ValueError: If validation fails
            PermissionError: If user lacks permission for global presets
            PresetValidationError: If YAML is invalid
        """
        # Validate randomizer type
        if randomizer not in self.SUPPORTED_RANDOMIZERS:
            raise ValueError(
                f"Unsupported randomizer: {randomizer}. "
                f"Supported: {', '.join(self.SUPPORTED_RANDOMIZERS)}"
            )

        # Check permissions for global presets
        if is_global and not user.has_permission(Permission.SUPERADMIN):
            raise PermissionError("Only SUPERADMIN can create global presets")

        # Validate and parse YAML
        settings_dict = self._validate_yaml(yaml_content)

        namespace_id = None
        if not is_global:
            # Get or create user's namespace
            namespace = await self.namespace_service.get_or_create_user_namespace(user)
            if not namespace:
                raise ValueError("Failed to create user namespace")
            namespace_id = namespace.id

        # Check for duplicate name
        existing = await self.repository.get_by_name(
            randomizer=randomizer,
            name=name,
            namespace_id=namespace_id
        )
        if existing:
            scope = "globally" if is_global else "in your namespace"
            raise ValueError(
                f"Preset '{name}' already exists for {randomizer} {scope}"
            )

        # Create preset
        preset = await self.repository.create(
            user_id=user.id,
            randomizer=randomizer,
            name=name,
            settings=settings_dict,
            namespace_id=namespace_id,
            description=description,
            is_public=is_public
        )

        scope = "global" if is_global else f"namespace {namespace_id}"
        logger.info(
            "User %s created preset %s for %s in %s (public=%s)",
            user.id,
            name,
            randomizer,
            scope,
            is_public
        )

        return preset

    async def update_preset(
        self,
        preset_id: int,
        user: User,
        yaml_content: Optional[str] = None,
        name: Optional[str] = None,
        description: Optional[str] = None,
        is_public: Optional[bool] = None
    ) -> RandomizerPreset:
        """
        Update a preset.

        Args:
            preset_id: Preset ID
            user: User performing the update
            yaml_content: Optional new YAML content
            name: Optional new name
            description: Optional new description
            is_public: Optional new public flag

        Returns:
            Updated RandomizerPreset

        Raises:
            ValueError: If preset not found or validation fails
            PermissionError: If user cannot edit preset
            PresetValidationError: If YAML is invalid
        """
        preset = await self.repository.get_by_id(preset_id)
        if not preset:
            raise ValueError("Preset not found")

        if not self._can_edit_preset(preset, user):
            raise PermissionError("Not authorized to edit this preset")

        # Build update dict
        updates = {}

        if yaml_content is not None:
            updates['settings'] = self._validate_yaml(yaml_content)

        if name is not None:
            # Check for duplicate if name is changing
            if name != preset.name:
                existing = await self.repository.get_by_name(
                    randomizer=preset.randomizer,
                    name=name,
                    namespace_id=preset.namespace_id
                )
                if existing and existing.id != preset_id:
                    scope = "globally" if preset.is_global else "in this namespace"
                    raise ValueError(
                        f"Preset '{name}' already exists for {preset.randomizer} {scope}"
                    )
            updates['name'] = name

        if description is not None:
            updates['description'] = description

        if is_public is not None:
            updates['is_public'] = is_public

        if not updates:
            return preset

        # Update preset
        updated_preset = await self.repository.update(preset_id, **updates)

        logger.info(
            "User %s updated preset %s (id=%s) fields: %s",
            user.id,
            preset.full_name,
            preset_id,
            list(updates.keys())
        )

        return updated_preset

    async def delete_preset(self, preset_id: int, user: User) -> bool:
        """
        Delete a preset.

        Args:
            preset_id: Preset ID
            user: User performing the deletion

        Returns:
            True if deleted

        Raises:
            ValueError: If preset not found
            PermissionError: If user cannot delete preset
        """
        preset = await self.repository.get_by_id(preset_id)
        if not preset:
            raise ValueError("Preset not found")

        if not self._can_edit_preset(preset, user):
            raise PermissionError("Not authorized to delete this preset")

        await self.repository.delete(preset_id)

        logger.info(
            "User %s deleted preset %s (id=%s)",
            user.id,
            preset.full_name,
            preset_id
        )

        return True

    def validate_yaml_content(self, yaml_content: str) -> dict:
        """
        Validate YAML content (public API).

        Args:
            yaml_content: YAML string to validate

        Returns:
            Parsed YAML as dict

        Raises:
            PresetValidationError: If YAML is invalid
        """
        return self._validate_yaml(yaml_content)

    def _validate_yaml(self, yaml_content: str) -> dict:
        """
        Validate and parse YAML content.

        Supports both SahasrahBot format (with settings + metadata) and raw settings.

        Args:
            yaml_content: YAML string to validate

        Returns:
            Settings dict

        Raises:
            PresetValidationError: If YAML is invalid
        """
        if not yaml_content or not yaml_content.strip():
            raise PresetValidationError("YAML content cannot be empty")

        try:
            parsed = yaml.safe_load(yaml_content)
        except yaml.YAMLError as e:
            raise PresetValidationError(f"Invalid YAML: {e}") from e

        if not isinstance(parsed, dict):
            raise PresetValidationError("YAML must be a dictionary/mapping")

        # If it has a 'settings' key (SahasrahBot format), extract it
        # Otherwise treat the whole thing as settings
        if 'settings' in parsed:
            settings = parsed['settings']
            if not isinstance(settings, dict):
                raise PresetValidationError("'settings' must be a dictionary")
            return parsed  # Store whole structure with metadata
        return parsed  # Store as-is
