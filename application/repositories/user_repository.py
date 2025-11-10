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
        permission: Permission = Permission.USER,
    ) -> User:
        """
        Create a new user.

        Args:
            discord_id: Discord user ID
            discord_username: Discord username
            discord_discriminator: Discord discriminator
            discord_avatar: Discord avatar hash
            permission: Initial permission level

        Returns:
            User: Created user
        """
        user = await User.create(
            discord_id=discord_id,
            discord_username=discord_username,
            discord_discriminator=discord_discriminator,
            discord_avatar=discord_avatar,
            permission=permission,
            is_active=True,
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
        return await query.order_by("-created_at")

    async def search_by_username(self, query: str) -> list[User]:
        """
        Search users by username.

        Args:
            query: Search query

        Returns:
            list[User]: List of matching users
        """
        return await User.filter(
            discord_username__icontains=query, is_active=True
        ).order_by("discord_username")

    async def get_admins(self) -> list[User]:
        """
        Get all admin users.

        Returns:
            list[User]: List of admin users
        """
        return await User.filter(
            permission__gte=Permission.ADMIN, is_active=True
        ).order_by("-permission")

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

    async def get_users_with_racetime(
        self,
        include_inactive: bool = False,
        limit: Optional[int] = None,
        offset: int = 0,
    ) -> list[User]:
        """
        Get all users with linked RaceTime accounts.

        Args:
            include_inactive: Whether to include inactive users
            limit: Maximum number of users to return
            offset: Number of users to skip

        Returns:
            list[User]: List of users with RaceTime accounts
        """
        query = User.filter(racetime_id__not_isnull=True)
        if not include_inactive:
            query = query.filter(is_active=True)

        query = query.order_by("-created_at")

        if offset > 0:
            query = query.offset(offset)
        if limit:
            query = query.limit(limit)

        return await query

    async def count_racetime_linked_users(self, include_inactive: bool = False) -> int:
        """
        Count users with linked RaceTime accounts.

        Args:
            include_inactive: Whether to include inactive users

        Returns:
            int: Number of users with linked RaceTime accounts
        """
        query = User.filter(racetime_id__not_isnull=True)
        if not include_inactive:
            query = query.filter(is_active=True)
        return await query.count()

    async def search_by_racetime_name(self, query: str) -> list[User]:
        """
        Search users by RaceTime username.

        Args:
            query: Search query

        Returns:
            list[User]: List of matching users
        """
        return await User.filter(
            racetime_name__icontains=query, racetime_id__not_isnull=True, is_active=True
        ).order_by("racetime_name")

    async def get_by_twitch_id(self, twitch_id: str) -> Optional[User]:
        """
        Get user by Twitch ID.

        Args:
            twitch_id: Twitch user ID

        Returns:
            Optional[User]: User if found, None otherwise
        """
        return await User.filter(twitch_id=twitch_id).first()

    async def get_users_with_twitch(
        self,
        include_inactive: bool = False,
        limit: Optional[int] = None,
        offset: int = 0,
    ) -> list[User]:
        """
        Get all users with linked Twitch accounts.

        Args:
            include_inactive: Whether to include inactive users
            limit: Maximum number of users to return
            offset: Number of users to skip

        Returns:
            list[User]: List of users with Twitch accounts
        """
        query = User.filter(twitch_id__not_isnull=True)
        if not include_inactive:
            query = query.filter(is_active=True)

        query = query.order_by("-created_at")

        if offset > 0:
            query = query.offset(offset)
        if limit:
            query = query.limit(limit)

        return await query

    async def count_twitch_linked_users(self, include_inactive: bool = False) -> int:
        """
        Count users with linked Twitch accounts.

        Args:
            include_inactive: Whether to include inactive users

        Returns:
            int: Number of users with linked Twitch accounts
        """
        query = User.filter(twitch_id__not_isnull=True)
        if not include_inactive:
            query = query.filter(is_active=True)
        return await query.count()

    async def search_by_twitch_name(self, query: str) -> list[User]:
        """
        Search users by Twitch username.

        Args:
            query: Search query

        Returns:
            list[User]: List of matching users
        """
        return await User.filter(
            twitch_name__icontains=query, twitch_id__not_isnull=True, is_active=True
        ).order_by("twitch_name")

    async def get_placeholder_users_for_tournament(
        self, tournament_id: int
    ) -> list[User]:
        """
        Get all placeholder users associated with a tournament's matches.

        This includes placeholders from both match players and crew.

        Args:
            tournament_id: Tournament ID

        Returns:
            list[User]: List of placeholder users
        """
        # Import here to avoid circular dependency
        from models.match_schedule import Match

        # Get all match IDs for this tournament
        matches = await Match.filter(tournament_id=tournament_id).values_list(
            "id", flat=True
        )
        match_ids = list(matches)

        if not match_ids:
            return []

        # Get placeholder users from match players
        player_placeholders = (
            await User.filter(
                is_placeholder=True, match_players__match_id__in=match_ids
            )
            .distinct()
            .prefetch_related("match_players__match")
        )

        # Get placeholder users from crew
        crew_placeholders = (
            await User.filter(
                is_placeholder=True, crew_memberships__match_id__in=match_ids
            )
            .distinct()
            .prefetch_related("crew_memberships__match")
        )

        # Combine and deduplicate, tracking roles
        all_placeholder_ids = set()
        all_placeholders = []

        for user in player_placeholders:
            if user.id not in all_placeholder_ids:
                all_placeholder_ids.add(user.id)
                # Tag user with role info for UI display
                user._placeholder_roles = ["Player"]
                all_placeholders.append(user)

        for user in crew_placeholders:
            if user.id not in all_placeholder_ids:
                all_placeholder_ids.add(user.id)
                # Tag user with role info for UI display
                user._placeholder_roles = ["Crew"]
                all_placeholders.append(user)
            else:
                # User is in both lists - add Crew to existing roles
                existing_user = next(u for u in all_placeholders if u.id == user.id)
                if "Crew" not in existing_user._placeholder_roles:
                    existing_user._placeholder_roles.append("Crew")

        return all_placeholders
