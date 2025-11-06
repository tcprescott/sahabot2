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
from application.services.randomizer.preset_namespace_service import PresetNamespaceService
from application.events import EventBus, PresetCreatedEvent, PresetUpdatedEvent

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
            include_global=include_global,
            user_id=user.id
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
                logger.error("Failed to create namespace for user %s", user.id)
                raise ValueError("Failed to create user namespace")
            namespace_id = namespace.id
            logger.info("Creating preset in namespace %s for user %s", namespace_id, user.id)
        else:
            logger.info("Creating global preset for user %s", user.id)

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
        
        # Also check if a global preset exists with this name (to avoid conflicts)
        if not is_global:
            global_existing = await self.repository.get_global_preset(
                randomizer=randomizer,
                name=name
            )
            if global_existing:
                raise ValueError(
                    f"A global preset named '{name}' already exists for {randomizer}. "
                    f"Please choose a different name to avoid conflicts."
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

        # Emit preset created event
        await EventBus.emit(PresetCreatedEvent(
            user_id=user.id,
            entity_id=preset.id,
            preset_name=name,
            namespace=f"namespace:{namespace_id}" if namespace_id else "global",
        ))

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

        # Emit preset updated event
        await EventBus.emit(PresetUpdatedEvent(
            user_id=user.id,
            entity_id=preset_id,
            preset_name=updated_preset.name,
            changed_fields=list(updates.keys()),
        ))

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

    async def list_user_presets(
        self,
        user: User,
        randomizer: Optional[str] = None,
        namespace_id: Optional[int] = None
    ) -> list[RandomizerPreset]:
        """
        List presets created by a specific user.

        Args:
            user: User whose presets to list
            randomizer: Optional randomizer filter
            namespace_id: Optional namespace filter

        Returns:
            List of user's presets
        """
        # Get user's namespace
        namespace = await self.namespace_service.get_or_create_user_namespace(user)
        if not namespace:
            return []

        # If namespace_id specified, use it; otherwise use user's namespace
        target_namespace_id = namespace_id if namespace_id is not None else namespace.id

        return await self.repository.list_in_namespace(
            namespace_id=target_namespace_id,
            randomizer=randomizer
        )

    async def list_public_presets(
        self,
        randomizer: Optional[str] = None,
        namespace_id: Optional[int] = None
    ) -> list[RandomizerPreset]:
        """
        List all public presets.

        Args:
            randomizer: Optional randomizer filter
            namespace_id: Optional namespace filter

        Returns:
            List of public presets
        """
        if namespace_id is not None:
            # Get presets from specific namespace that are public
            presets = await self.repository.list_in_namespace(
                namespace_id=namespace_id,
                randomizer=randomizer
            )
            return [p for p in presets if p.is_public]

        # Get all global public presets
        return await self.repository.list_global_presets(randomizer=randomizer)

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

        # Detect mystery preset
        is_mystery = self._is_mystery_preset(parsed)

        # If mystery preset, validate mystery structure
        if is_mystery:
            self._validate_mystery_preset(parsed)
            # Tag it as mystery preset if not already tagged
            if 'preset_type' not in parsed:
                parsed['preset_type'] = 'mystery'

        # If it has a 'settings' key (SahasrahBot format), extract it
        # Otherwise treat the whole thing as settings
        if 'settings' in parsed:
            settings = parsed['settings']
            if not isinstance(settings, dict):
                raise PresetValidationError("'settings' must be a dictionary")
            return parsed  # Store whole structure with metadata
        return parsed  # Store as-is

    def _is_mystery_preset(self, parsed: dict) -> bool:
        """
        Check if a parsed YAML is a mystery preset.

        Mystery presets have:
        - 'preset_type' == 'mystery' OR
        - 'weights' key OR
        - 'mystery_weights' key

        Args:
            parsed: Parsed YAML dict

        Returns:
            True if mystery preset
        """
        # Explicit mystery type
        if parsed.get('preset_type') == 'mystery':
            return True

        # Has weights or mystery_weights
        if 'weights' in parsed or 'mystery_weights' in parsed:
            return True

        # Check in 'settings' sub-dict (SahasrahBot format)
        if 'settings' in parsed:
            settings = parsed['settings']
            if isinstance(settings, dict):
                if 'weights' in settings or 'mystery_weights' in settings:
                    return True

        return False

    def _validate_mystery_preset(self, parsed: dict) -> None:
        """
        Validate mystery preset structure.

        Args:
            parsed: Parsed YAML dict

        Raises:
            PresetValidationError: If mystery preset is invalid
        """
        from application.services.randomizer.alttpr_mystery_service import ALTTPRMysteryService

        # Extract mystery weights (could be at root or in 'mystery_weights' key)
        mystery_weights = parsed.get('mystery_weights', parsed)

        # If the expected weight keys are not present in the current mystery_weights,
        # and the preset uses SahasrahBot format (with a 'settings' key), check for weights inside 'settings'.
        expected_weight_keys = ['weights', 'entrance_weights', 'customizer']
        has_expected_keys = any(k in mystery_weights for k in expected_weight_keys)
        if 'settings' in parsed and not has_expected_keys:
            mystery_weights = parsed['settings']

        # Validate using mystery service
        service = ALTTPRMysteryService()
        is_valid, error_message = service.validate_mystery_weights(mystery_weights)

        if not is_valid:
            raise PresetValidationError(f"Invalid mystery preset: {error_message}")
