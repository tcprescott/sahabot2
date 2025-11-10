"""Repository for Discord guild data access."""

from __future__ import annotations
from typing import Optional, List
import logging

from models.discord_guild import DiscordGuild

logger = logging.getLogger(__name__)


class DiscordGuildRepository:
    """Data access methods for Discord guilds."""

    async def get_by_guild_id(self, guild_id: int) -> Optional[DiscordGuild]:
        """
        Get a Discord guild by its Discord guild ID.

        Note: This returns the first match. Since guilds can be linked to multiple
        organizations, use get_guild(organization_id, guild_id) for organization-specific lookup.
        """
        return await DiscordGuild.get_or_none(guild_id=guild_id).prefetch_related(
            "organization", "linked_by"
        )

    async def get_guild(
        self, organization_id: int, guild_id: int
    ) -> Optional[DiscordGuild]:
        """Get a Discord guild for a specific organization."""
        return await DiscordGuild.get_or_none(
            organization_id=organization_id, guild_id=guild_id
        ).prefetch_related("organization", "linked_by")

    async def get_by_id(self, guild_pk: int) -> Optional[DiscordGuild]:
        """Get a Discord guild by primary key."""
        return await DiscordGuild.get_or_none(id=guild_pk).prefetch_related(
            "organization", "linked_by"
        )

    async def list_by_organization(self, organization_id: int) -> List[DiscordGuild]:
        """List all Discord guilds for an organization."""
        return (
            await DiscordGuild.filter(organization_id=organization_id, is_active=True)
            .prefetch_related("linked_by")
            .all()
        )

    async def create(
        self,
        organization_id: int,
        guild_id: int,
        guild_name: str,
        guild_icon: Optional[str],
        linked_by_user_id: int,
        verified_admin: bool = False,
    ) -> DiscordGuild:
        """Create a new Discord guild link."""
        guild = await DiscordGuild.create(
            organization_id=organization_id,
            guild_id=guild_id,
            guild_name=guild_name,
            guild_icon=guild_icon,
            linked_by_id=linked_by_user_id,
            verified_admin=verified_admin,
            is_active=True,
        )
        logger.info(
            "Created Discord guild link %s for org %s", guild_id, organization_id
        )
        return guild

    async def update(self, guild_pk: int, **fields) -> Optional[DiscordGuild]:
        """Update a Discord guild."""
        guild = await self.get_by_id(guild_pk)
        if not guild:
            return None

        for field, value in fields.items():
            if hasattr(guild, field):
                setattr(guild, field, value)

        await guild.save()
        logger.info("Updated Discord guild %s", guild_pk)
        return guild

    async def delete(self, guild_pk: int) -> bool:
        """Delete a Discord guild link."""
        guild = await self.get_by_id(guild_pk)
        if not guild:
            return False

        await guild.delete()
        logger.info("Deleted Discord guild %s", guild_pk)
        return True

    async def deactivate(self, guild_id: int) -> Optional[DiscordGuild]:
        """Mark a guild as inactive (bot left the server)."""
        from datetime import datetime, timezone

        guild = await self.get_by_guild_id(guild_id)
        if not guild:
            return None

        guild.is_active = False
        guild.bot_left_at = datetime.now(timezone.utc)
        await guild.save()

        logger.info("Deactivated Discord guild %s", guild_id)
        return guild

    async def get_guilds_by_organization(
        self, organization_id: int, active_only: bool = True
    ) -> List[DiscordGuild]:
        """
        Get all Discord guilds for an organization.

        Args:
            organization_id: Organization ID
            active_only: Only return active guilds

        Returns:
            List of DiscordGuild models
        """
        query = DiscordGuild.filter(organization_id=organization_id)
        if active_only:
            query = query.filter(is_active=True)
        return await query.prefetch_related("linked_by").all()

    async def get_guilds_by_ids(
        self, guild_ids: List[int], organization_id: int
    ) -> List[DiscordGuild]:
        """
        Get Discord guilds by their primary key IDs for a specific organization.

        Args:
            guild_ids: List of DiscordGuild primary key IDs
            organization_id: Organization ID (for security)

        Returns:
            List of DiscordGuild models
        """
        return (
            await DiscordGuild.filter(id__in=guild_ids, organization_id=organization_id)
            .prefetch_related("linked_by")
            .all()
        )
