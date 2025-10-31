"""
User service for user-related business logic.

This module contains all business logic related to user management.
"""

from models import User, Permission
from typing import Optional
from application.repositories.user_repository import UserRepository


class UserService:
    """
    Service for handling user-related business logic.
    
    This service encapsulates all business rules and operations related to users,
    keeping the logic separate from the UI and data access layers.
    """
    
    def __init__(self):
        """Initialize the user service with required repositories."""
        self.user_repository = UserRepository()
    
    async def get_or_create_user_from_discord(
        self,
        discord_id: int,
        discord_username: str,
        discord_discriminator: Optional[str] = None,
        discord_avatar: Optional[str] = None,
        discord_email: Optional[str] = None
    ) -> User:
        """
        Get or create a user from Discord OAuth data.
        
        Args:
            discord_id: Discord user ID
            discord_username: Discord username
            discord_discriminator: Discord discriminator
            discord_avatar: Discord avatar hash
            discord_email: Discord email
            
        Returns:
            User: The existing or newly created user
        """
        user = await self.user_repository.get_by_discord_id(discord_id)
        
        if user:
            # Update user information if it has changed
            updated = False
            if user.discord_username != discord_username:
                user.discord_username = discord_username
                updated = True
            if discord_discriminator and user.discord_discriminator != discord_discriminator:
                user.discord_discriminator = discord_discriminator
                updated = True
            if discord_avatar and user.discord_avatar != discord_avatar:
                user.discord_avatar = discord_avatar
                updated = True
            if discord_email and user.discord_email != discord_email:
                user.discord_email = discord_email
                updated = True
            
            if updated:
                await user.save()
            
            return user
        
        # Create new user with default USER permission
        user = await self.user_repository.create(
            discord_id=discord_id,
            discord_username=discord_username,
            discord_discriminator=discord_discriminator,
            discord_avatar=discord_avatar,
            discord_email=discord_email,
            permission=Permission.USER
        )
        
        return user

    async def create_user_manual(
        self,
        discord_id: int,
        discord_username: str,
        discord_email: Optional[str] = None,
        permission: Permission = Permission.USER,
        is_active: bool = True,
        discord_discriminator: Optional[str] = None,
        discord_avatar: Optional[str] = None,
    ) -> User:
        """Create a user manually.

        Validates uniqueness by Discord ID and applies defaults consistent with
        OAuth-created users.

        Args:
            discord_id: Discord user ID (unique)
            discord_username: Display username
            discord_email: Optional email
            permission: Initial permission level (default USER)
            is_active: Whether the account is active (default True)
            discord_discriminator: Optional discriminator (legacy)
            discord_avatar: Optional avatar hash

        Returns:
            User: The newly created user

        Raises:
            ValueError: If a user with the given Discord ID already exists
        """
        # Ensure required fields
        if not discord_id or not discord_username:
            raise ValueError("discord_id and discord_username are required")

        existing = await self.user_repository.get_by_discord_id(discord_id)
        if existing:
            raise ValueError("A user with this Discord ID already exists")

        # Create via repository; default is_active True, override if specified
        user = await self.user_repository.create(
            discord_id=discord_id,
            discord_username=discord_username,
            discord_discriminator=discord_discriminator,
            discord_avatar=discord_avatar,
            discord_email=discord_email,
            permission=permission,
        )

        if user.is_active != is_active:
            user.is_active = is_active
            await user.save()

        return user
    
    async def update_user_permission(self, user_id: int, new_permission: Permission) -> User:
        """
        Update a user's permission level.
        
        Args:
            user_id: ID of the user to update
            new_permission: New permission level
            
        Returns:
            User: Updated user
            
        Raises:
            ValueError: If user not found
        """
        user = await self.user_repository.get_by_id(user_id)
        if not user:
            raise ValueError(f"User with ID {user_id} not found")
        
        user.permission = new_permission
        await user.save()
        
        return user
    
    async def deactivate_user(self, user_id: int) -> User:
        """
        Deactivate a user account.
        
        Args:
            user_id: ID of the user to deactivate
            
        Returns:
            User: Deactivated user
            
        Raises:
            ValueError: If user not found
        """
        user = await self.user_repository.get_by_id(user_id)
        if not user:
            raise ValueError(f"User with ID {user_id} not found")
        
        user.is_active = False
        await user.save()
        
        return user
    
    async def activate_user(self, user_id: int) -> User:
        """
        Activate a user account.
        
        Args:
            user_id: ID of the user to activate
            
        Returns:
            User: Activated user
            
        Raises:
            ValueError: If user not found
        """
        user = await self.user_repository.get_by_id(user_id)
        if not user:
            raise ValueError(f"User with ID {user_id} not found")
        
        user.is_active = True
        await user.save()
        
        return user
    
    async def get_all_users(self, include_inactive: bool = False) -> list[User]:
        """
        Get all users.
        
        Args:
            include_inactive: Whether to include inactive users
            
        Returns:
            list[User]: List of users
        """
        return await self.user_repository.get_all(include_inactive=include_inactive)
    
    async def search_users(self, query: str) -> list[User]:
        """
        Search users by username.
        
        Args:
            query: Search query
            
        Returns:
            list[User]: List of matching users
        """
        return await self.user_repository.search_by_username(query)
