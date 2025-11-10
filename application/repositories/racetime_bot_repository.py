"""
RaceTime Bot repository.

Data access layer for RaceTime bot management.
"""

import logging
from datetime import datetime, timezone
from typing import Optional
from models import RacetimeBot, RacetimeBotOrganization, Organization, BotStatus

logger = logging.getLogger(__name__)


class RacetimeBotRepository:
    """Repository for RaceTime bot data access."""

    async def get_all_bots(self) -> list[RacetimeBot]:
        """
        Get all RaceTime bots.

        Returns:
            List of all RaceTime bots ordered by category
        """
        return await RacetimeBot.all().order_by("category")

    async def get_active_bots(self) -> list[RacetimeBot]:
        """
        Get all active RaceTime bots.

        Returns:
            List of active RaceTime bots ordered by category
        """
        return await RacetimeBot.filter(is_active=True).order_by("category")

    async def get_bot_by_id(self, bot_id: int) -> Optional[RacetimeBot]:
        """
        Get a RaceTime bot by ID.

        Args:
            bot_id: Bot ID

        Returns:
            RaceTime bot or None if not found
        """
        return await RacetimeBot.filter(id=bot_id).first()

    async def get_bot_by_category(self, category: str) -> Optional[RacetimeBot]:
        """
        Get a RaceTime bot by category.

        Args:
            category: RaceTime category slug

        Returns:
            RaceTime bot or None if not found
        """
        return await RacetimeBot.filter(category=category).first()

    async def create_bot(
        self,
        category: str,
        client_id: str,
        client_secret: str,
        name: str,
        description: Optional[str] = None,
        is_active: bool = True,
        handler_class: str = "SahaRaceHandler",
    ) -> RacetimeBot:
        """
        Create a new RaceTime bot.

        Args:
            category: RaceTime category slug (e.g., 'alttpr')
            client_id: OAuth2 client ID
            client_secret: OAuth2 client secret
            name: Friendly name for the bot
            description: Optional description
            is_active: Whether the bot is active
            handler_class: Handler class name (default: 'SahaRaceHandler')

        Returns:
            Created RaceTime bot
        """
        bot = await RacetimeBot.create(
            category=category,
            client_id=client_id,
            client_secret=client_secret,
            name=name,
            description=description,
            is_active=is_active,
            handler_class=handler_class,
        )
        logger.info(
            "Created RaceTime bot: %s (category: %s, handler: %s)",
            name,
            category,
            handler_class,
        )
        return bot

    async def update_bot(
        self,
        bot_id: int,
        **updates,
    ) -> Optional[RacetimeBot]:
        """
        Update a RaceTime bot.

        Args:
            bot_id: Bot ID
            **updates: Fields to update

        Returns:
            Updated bot or None if not found
        """
        bot = await self.get_bot_by_id(bot_id)
        if not bot:
            return None

        await bot.update_from_dict(updates).save()
        logger.info("Updated RaceTime bot %s: %s", bot_id, list(updates.keys()))
        return bot

    async def delete_bot(self, bot_id: int) -> bool:
        """
        Delete a RaceTime bot.

        Args:
            bot_id: Bot ID

        Returns:
            True if deleted, False if not found
        """
        bot = await self.get_bot_by_id(bot_id)
        if not bot:
            return False

        # Delete all organization assignments first
        await RacetimeBotOrganization.filter(bot_id=bot_id).delete()

        await bot.delete()
        logger.info("Deleted RaceTime bot: %s", bot_id)
        return True

    async def get_bots_for_organization(
        self, organization_id: int, active_only: bool = True
    ) -> list[RacetimeBot]:
        """
        Get RaceTime bots assigned to an organization.

        Args:
            organization_id: Organization ID
            active_only: If True, only return active assignments

        Returns:
            List of RaceTime bots assigned to the organization
        """
        query = RacetimeBotOrganization.filter(organization_id=organization_id)
        if active_only:
            query = query.filter(is_active=True, bot__is_active=True)

        assignments = await query.prefetch_related("bot")
        return [assignment.bot for assignment in assignments]

    async def get_organizations_for_bot(self, bot_id: int) -> list[Organization]:
        """
        Get organizations assigned to a RaceTime bot.

        Args:
            bot_id: Bot ID

        Returns:
            List of organizations assigned to the bot
        """
        assignments = await RacetimeBotOrganization.filter(
            bot_id=bot_id, is_active=True
        ).prefetch_related("organization")
        return [assignment.organization for assignment in assignments]

    async def assign_bot_to_organization(
        self, bot_id: int, organization_id: int, is_active: bool = True
    ) -> RacetimeBotOrganization:
        """
        Assign a RaceTime bot to an organization.

        Args:
            bot_id: Bot ID
            organization_id: Organization ID
            is_active: Whether the assignment is active

        Returns:
            Created or updated assignment
        """
        assignment, created = await RacetimeBotOrganization.get_or_create(
            bot_id=bot_id,
            organization_id=organization_id,
            defaults={"is_active": is_active},
        )

        if not created and assignment.is_active != is_active:
            assignment.is_active = is_active
            await assignment.save()

        logger.info(
            "%s RaceTime bot %s to organization %s",
            "Assigned" if created else "Updated assignment of",
            bot_id,
            organization_id,
        )
        return assignment

    async def unassign_bot_from_organization(
        self, bot_id: int, organization_id: int
    ) -> bool:
        """
        Remove a RaceTime bot assignment from an organization.

        Args:
            bot_id: Bot ID
            organization_id: Organization ID

        Returns:
            True if deleted, False if not found
        """
        deleted_count = await RacetimeBotOrganization.filter(
            bot_id=bot_id, organization_id=organization_id
        ).delete()

        if deleted_count > 0:
            logger.info(
                "Unassigned RaceTime bot %s from organization %s",
                bot_id,
                organization_id,
            )
        return deleted_count > 0

    async def get_assignment(
        self, bot_id: int, organization_id: int
    ) -> Optional[RacetimeBotOrganization]:
        """
        Get a specific bot-organization assignment.

        Args:
            bot_id: Bot ID
            organization_id: Organization ID

        Returns:
            Assignment or None if not found
        """
        return await RacetimeBotOrganization.filter(
            bot_id=bot_id, organization_id=organization_id
        ).first()

    async def update_bot_status(
        self,
        bot_id: int,
        status: BotStatus,
        status_message: Optional[str] = None,
    ) -> Optional[RacetimeBot]:
        """
        Update a bot's status.

        Args:
            bot_id: Bot ID
            status: New status
            status_message: Optional status message (e.g., error details)

        Returns:
            Updated bot or None if not found
        """
        bot = await self.get_bot_by_id(bot_id)
        if not bot:
            return None

        bot.status = status
        bot.status_message = status_message
        bot.last_status_check_at = datetime.now(timezone.utc)

        if status == BotStatus.CONNECTED:
            bot.last_connected_at = datetime.now(timezone.utc)

        await bot.save()
        logger.info(
            "Updated bot %s status to %s: %s",
            bot_id,
            bot.get_status_display(),
            status_message or "No message",
        )
        return bot

    async def record_connection_success(self, bot_id: int) -> Optional[RacetimeBot]:
        """
        Record a successful bot connection.

        Args:
            bot_id: Bot ID

        Returns:
            Updated bot or None if not found
        """
        return await self.update_bot_status(
            bot_id, BotStatus.CONNECTED, status_message=None
        )

    async def record_connection_failure(
        self, bot_id: int, error: str, status: BotStatus = BotStatus.CONNECTION_ERROR
    ) -> Optional[RacetimeBot]:
        """
        Record a bot connection failure.

        Args:
            bot_id: Bot ID
            error: Error message
            status: Failure status (AUTH_FAILED or CONNECTION_ERROR)

        Returns:
            Updated bot or None if not found
        """
        return await self.update_bot_status(bot_id, status, status_message=error)

    async def get_unhealthy_bots(self) -> list[RacetimeBot]:
        """
        Get all bots with non-healthy status.

        Returns:
            List of bots that are not CONNECTED
        """
        return (
            await RacetimeBot.filter(is_active=True)
            .exclude(status=BotStatus.CONNECTED)
            .order_by("category")
        )
