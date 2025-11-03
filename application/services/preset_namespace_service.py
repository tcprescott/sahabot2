"""
Preset namespace service for business logic.

This module handles business logic for managing preset namespaces,
including authorization, validation, and automatic namespace creation.
"""

import logging
import re
from typing import Optional
from models import User, PresetNamespace
from application.repositories.preset_namespace_repository import PresetNamespaceRepository

logger = logging.getLogger(__name__)


class NamespaceValidationError(Exception):
    """Exception raised when namespace validation fails."""


class PresetNamespaceService:
    """Service for managing preset namespaces."""

    # Namespace name validation: lowercase alphanumeric, hyphens, underscores
    NAMESPACE_NAME_PATTERN = re.compile(r'^[a-z0-9_-]+$')
    MIN_NAME_LENGTH = 3
    MAX_NAME_LENGTH = 50

    def __init__(self):
        """Initialize the namespace service."""
        self.repository = PresetNamespaceRepository()

    def _validate_namespace_name(self, name: str) -> None:
        """
        Validate namespace name.

        Args:
            name: Namespace name to validate

        Raises:
            NamespaceValidationError: If validation fails
        """
        if not name:
            raise NamespaceValidationError("Namespace name cannot be empty")

        if len(name) < self.MIN_NAME_LENGTH:
            raise NamespaceValidationError(
                f"Namespace name must be at least {self.MIN_NAME_LENGTH} characters"
            )

        if len(name) > self.MAX_NAME_LENGTH:
            raise NamespaceValidationError(
                f"Namespace name must be at most {self.MAX_NAME_LENGTH} characters"
            )

        if not self.NAMESPACE_NAME_PATTERN.match(name):
            raise NamespaceValidationError(
                "Namespace name can only contain lowercase letters, numbers, hyphens, and underscores"
            )

        # Reserved names
        reserved = {'admin', 'api', 'public', 'private', 'system', 'root', 'user', 'org', 'organization'}
        if name in reserved:
            raise NamespaceValidationError(f"Namespace name '{name}' is reserved")

    async def get_or_create_user_namespace(
        self,
        user: User,
        auto_create: bool = True
    ) -> Optional[PresetNamespace]:
        """
        Get or create a user's personal namespace.

        If the user doesn't have a namespace and auto_create is True,
        one will be created automatically using their Discord username.

        Args:
            user: User to get/create namespace for
            auto_create: Whether to auto-create if not found

        Returns:
            PresetNamespace if found/created, None if not found and auto_create=False
        """
        # Check if user already has a namespace
        namespace = await self.repository.get_user_namespace(user)
        if namespace:
            return namespace

        if not auto_create:
            return None

        # Auto-create namespace using Discord username
        # Sanitize username to be namespace-compatible
        base_name = user.discord_username.lower()
        base_name = re.sub(r'[^a-z0-9_-]', '-', base_name)
        base_name = re.sub(r'-+', '-', base_name)  # Collapse multiple hyphens
        base_name = base_name.strip('-')

        # Ensure it meets length requirements
        if len(base_name) < self.MIN_NAME_LENGTH:
            base_name = f"user-{user.id}"

        # Check if name is taken
        name = base_name
        counter = 1
        while await self.repository.get_by_name(name):
            name = f"{base_name}-{counter}"
            counter += 1

        # Create namespace
        try:
            namespace = await self.repository.create_user_namespace(
                user=user,
                name=name,
                display_name=user.discord_username,
                description=f"Personal preset namespace for {user.discord_username}",
                is_public=True
            )
            logger.info(
                "Auto-created namespace '%s' for user %s",
                name,
                user.id
            )
            return namespace
        except Exception as e:
            logger.error(
                "Failed to auto-create namespace for user %s: %s",
                user.id,
                e,
                exc_info=True
            )
            return None

    async def get_namespace(self, namespace_id: int) -> Optional[PresetNamespace]:
        """
        Get a namespace by ID.

        Args:
            namespace_id: Namespace ID

        Returns:
            PresetNamespace if found, None otherwise
        """
        return await self.repository.get_by_id(namespace_id)

    async def get_namespace_by_name(self, name: str) -> Optional[PresetNamespace]:
        """
        Get a namespace by name.

        Args:
            name: Namespace name

        Returns:
            PresetNamespace if found, None otherwise
        """
        return await self.repository.get_by_name(name)

    async def list_accessible_namespaces(self, user: Optional[User] = None) -> list[PresetNamespace]:
        """
        List namespaces accessible to a user.

        Args:
            user: Optional user (if None, only public namespaces returned)

        Returns:
            List of accessible namespaces
        """
        if user:
            return await self.repository.list_user_accessible_namespaces(user)
        return await self.repository.list_public_namespaces()

    async def create_user_namespace(
        self,
        user: User,
        name: str,
        display_name: str,
        description: Optional[str] = None,
        is_public: bool = True
    ) -> PresetNamespace:
        """
        Create a personal namespace for a user.

        Args:
            user: User creating the namespace
            name: Namespace identifier
            display_name: Human-friendly name
            description: Optional description
            is_public: Whether namespace is public

        Returns:
            Created PresetNamespace

        Raises:
            NamespaceValidationError: If validation fails
            ValueError: If namespace name already exists
        """
        # Validate name
        self._validate_namespace_name(name)

        # Check for duplicates
        existing = await self.repository.get_by_name(name)
        if existing:
            raise ValueError(f"Namespace '{name}' already exists")

        # Check if user already has a namespace
        user_namespace = await self.repository.get_user_namespace(user)
        if user_namespace:
            raise ValueError("User already has a namespace")

        return await self.repository.create_user_namespace(
            user=user,
            name=name,
            display_name=display_name,
            description=description,
            is_public=is_public
        )

    async def update_namespace(
        self,
        namespace_id: int,
        user: User,
        display_name: Optional[str] = None,
        description: Optional[str] = None,
        is_public: Optional[bool] = None
    ) -> PresetNamespace:
        """
        Update a namespace.

        Args:
            namespace_id: Namespace ID
            user: User performing the update
            display_name: Optional new display name
            description: Optional new description
            is_public: Optional new public flag

        Returns:
            Updated PresetNamespace

        Raises:
            ValueError: If namespace not found
            PermissionError: If user cannot edit namespace
        """
        namespace = await self.repository.get_by_id(namespace_id)
        if not namespace:
            raise ValueError("Namespace not found")

        if not await namespace.can_user_edit(user):
            raise PermissionError("Not authorized to edit this namespace")

        updates = {}
        if display_name is not None:
            updates['display_name'] = display_name
        if description is not None:
            updates['description'] = description
        if is_public is not None:
            updates['is_public'] = is_public

        if not updates:
            return namespace

        updated_namespace = await self.repository.update(namespace_id, **updates)
        logger.info(
            "User %s updated namespace '%s' (id=%s)",
            user.id,
            namespace.name,
            namespace_id
        )
        return updated_namespace

    async def can_user_edit_namespace(
        self,
        namespace_id: int,
        user: User
    ) -> bool:
        """
        Check if user can edit a namespace.

        Args:
            namespace_id: Namespace ID
            user: User to check

        Returns:
            True if user can edit the namespace
        """
        namespace = await self.repository.get_by_id(namespace_id)
        if not namespace:
            return False

        return await namespace.can_user_edit(user)
