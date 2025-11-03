"""
Preset namespace repository for data access.

This module handles all database operations for preset namespaces.
"""

import logging
from typing import Optional
from models import PresetNamespace, User, Organization

logger = logging.getLogger(__name__)


class PresetNamespaceRepository:
    """Repository for preset namespace data access operations."""

    async def get_by_id(self, namespace_id: int) -> Optional[PresetNamespace]:
        """
        Get a namespace by ID.

        Args:
            namespace_id: Namespace ID

        Returns:
            PresetNamespace if found, None otherwise
        """
        return await PresetNamespace.get_or_none(id=namespace_id).prefetch_related('user', 'organization')

    async def get_by_name(self, name: str) -> Optional[PresetNamespace]:
        """
        Get a namespace by name.

        Args:
            name: Namespace name (unique identifier)

        Returns:
            PresetNamespace if found, None otherwise
        """
        return await PresetNamespace.get_or_none(name=name).prefetch_related('user', 'organization')

    async def get_user_namespace(self, user: User) -> Optional[PresetNamespace]:
        """
        Get a user's personal namespace.

        Args:
            user: User to get namespace for

        Returns:
            PresetNamespace if found, None otherwise
        """
        return await PresetNamespace.get_or_none(user=user).prefetch_related('user', 'organization')

    async def get_organization_namespace(self, organization: Organization) -> Optional[PresetNamespace]:
        """
        Get an organization's namespace.

        Args:
            organization: Organization to get namespace for

        Returns:
            PresetNamespace if found, None otherwise
        """
        return await PresetNamespace.get_or_none(organization=organization).prefetch_related('user', 'organization')

    async def list_public_namespaces(self) -> list[PresetNamespace]:
        """
        List all public namespaces.

        Returns:
            List of public namespaces
        """
        return await PresetNamespace.filter(is_public=True).prefetch_related('user', 'organization').order_by('name')

    async def list_user_accessible_namespaces(self, user: User) -> list[PresetNamespace]:
        """
        List all namespaces accessible to a user.

        This includes:
        - User's own namespace
        - Public namespaces
        - TODO: Organization namespaces user is member of

        Args:
            user: User to get accessible namespaces for

        Returns:
            List of accessible namespaces
        """
        # Get user's own namespace + public ones
        namespaces = await PresetNamespace.filter(
            user=user
        ).prefetch_related('user', 'organization')

        public_namespaces = await PresetNamespace.filter(
            is_public=True
        ).prefetch_related('user', 'organization')

        # Combine and deduplicate
        all_namespaces = {ns.id: ns for ns in namespaces + public_namespaces}
        return list(all_namespaces.values())

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
            user: User who owns the namespace
            name: Unique namespace identifier
            display_name: Human-friendly display name
            description: Optional description
            is_public: Whether namespace is publicly visible

        Returns:
            Created PresetNamespace
        """
        namespace = await PresetNamespace.create(
            user=user,
            name=name,
            display_name=display_name,
            description=description,
            is_public=is_public
        )
        await namespace.fetch_related('user', 'organization')
        logger.info(
            "Created user namespace '%s' for user %s",
            name,
            user.id
        )
        return namespace

    async def create_organization_namespace(
        self,
        organization: Organization,
        name: str,
        display_name: str,
        description: Optional[str] = None,
        is_public: bool = True
    ) -> PresetNamespace:
        """
        Create a namespace for an organization.

        Args:
            organization: Organization that owns the namespace
            name: Unique namespace identifier
            display_name: Human-friendly display name
            description: Optional description
            is_public: Whether namespace is publicly visible

        Returns:
            Created PresetNamespace
        """
        namespace = await PresetNamespace.create(
            organization=organization,
            name=name,
            display_name=display_name,
            description=description,
            is_public=is_public
        )
        await namespace.fetch_related('user', 'organization')
        logger.info(
            "Created organization namespace '%s' for organization %s",
            name,
            organization.id
        )
        return namespace

    async def update(self, namespace_id: int, **fields) -> Optional[PresetNamespace]:
        """
        Update a namespace.

        Args:
            namespace_id: Namespace ID
            **fields: Fields to update

        Returns:
            Updated PresetNamespace if found, None otherwise
        """
        namespace = await self.get_by_id(namespace_id)
        if not namespace:
            return None

        # Only allow updating specific fields
        allowed_fields = {'display_name', 'description', 'is_public'}
        update_fields = {k: v for k, v in fields.items() if k in allowed_fields}

        if update_fields:
            await namespace.update_from_dict(update_fields)
            await namespace.save()
            logger.info(
                "Updated namespace '%s' (id=%s) fields: %s",
                namespace.name,
                namespace_id,
                list(update_fields.keys())
            )

        return namespace

    async def delete(self, namespace_id: int) -> bool:
        """
        Delete a namespace.

        Note: This will fail if there are presets in the namespace due to FK constraints.

        Args:
            namespace_id: Namespace ID

        Returns:
            True if deleted, False if not found
        """
        namespace = await self.get_by_id(namespace_id)
        if not namespace:
            return False

        logger.info("Deleting namespace '%s' (id=%s)", namespace.name, namespace_id)
        await namespace.delete()
        return True
