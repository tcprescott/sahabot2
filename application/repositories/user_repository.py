"""
User repository for data access.

This module provides data access methods for User model.
"""

from models import User, Permission
from typing import Optional


class UserRepository:
    """
    Repository for User data access.

    This class encapsulates all database operations for User model,
    separating data access from business logic.
    """

    async def get_by_id(self, user_id: int) -> Optional[User]:
        """
        Get user by ID.

        Args:
            user_id: User ID

        Returns:
            Optional[User]: User if found, None otherwise
        """
        return await User.filter(id=user_id).first()

    async def get_by_discord_id(self, discord_id: int) -> Optional[User]:
        """
        Get user by Discord ID.

        Args:
            discord_id: Discord user ID

        Returns:
            Optional[User]: User if found, None otherwise
        """
        return await User.filter(discord_id=discord_id).first()

    async def create(
        self,
        discord_id: int,
        discord_username: str,
        discord_discriminator: Optional[str] = None,
        discord_avatar: Optional[str] = None,
        discord_email: Optional[str] = None,
        permission: Permission = Permission.USER
    ) -> User:
        """
        Create a new user.

        Args:
            discord_id: Discord user ID
            discord_username: Discord username
            discord_discriminator: Discord discriminator
            discord_avatar: Discord avatar hash
            discord_email: Discord email
            permission: Initial permission level

        Returns:
            User: Created user
        """
        user = await User.create(
            discord_id=discord_id,
            discord_username=discord_username,
            discord_discriminator=discord_discriminator,
            discord_avatar=discord_avatar,
            discord_email=discord_email,
            permission=permission,
            is_active=True
        )
        return user

    async def get_all(self, include_inactive: bool = False) -> list[User]:
        """
        Get all users.

        Args:
            include_inactive: Whether to include inactive users

        Returns:
            list[User]: List of users
        """
        query = User.all()
        if not include_inactive:
            query = query.filter(is_active=True)
        return await query.order_by('-created_at')

    async def search_by_username(self, query: str) -> list[User]:
        """
        Search users by username.

        Args:
            query: Search query

        Returns:
            list[User]: List of matching users
        """
        return await User.filter(
            discord_username__icontains=query,
            is_active=True
        ).order_by('discord_username')

    async def get_admins(self) -> list[User]:
        """
        Get all admin users.

        Returns:
            list[User]: List of admin users
        """
        return await User.filter(
            permission__gte=Permission.ADMIN,
            is_active=True
        ).order_by('-permission')

    async def count_active_users(self) -> int:
        """
        Count active users.

        Returns:
            int: Number of active users
        """
        return await User.filter(is_active=True).count()

    async def get_by_racetime_id(self, racetime_id: str) -> Optional[User]:
        """
        Get user by RaceTime.gg ID.

        Args:
            racetime_id: RaceTime.gg user ID

        Returns:
            Optional[User]: User if found, None otherwise
        """
        return await User.filter(racetime_id=racetime_id).first()

