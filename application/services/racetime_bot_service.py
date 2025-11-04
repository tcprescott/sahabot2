"""
RaceTime Bot service.

Business logic for managing RaceTime bots and their organization assignments.
"""
import logging
from typing import Optional
from models import User, Permission, RacetimeBot, RacetimeBotOrganization, Organization
from application.repositories.racetime_bot_repository import RacetimeBotRepository
from application.repositories.organization_repository import OrganizationRepository
from application.services.authorization_service import AuthorizationService
from application.events import (
    EventBus,
    RacetimeBotCreatedEvent,
    RacetimeBotUpdatedEvent,
    RacetimeBotDeletedEvent,
)

logger = logging.getLogger(__name__)


class RacetimeBotService:
    """Service for managing RaceTime bots."""

    def __init__(self):
        self.repository = RacetimeBotRepository()
        self.org_repository = OrganizationRepository()
        self.auth_service = AuthorizationService()

    async def get_all_bots(self, current_user: Optional[User]) -> list[RacetimeBot]:
        """
        Get all RaceTime bots.

        Authorization: Only ADMIN and SUPERADMIN can view all bots.

        Args:
            current_user: Current user

        Returns:
            List of all bots (or empty list if unauthorized)
        """
        if not current_user or not self.auth_service.can_access_admin_panel(
            current_user
        ):
            logger.warning(
                "Unauthorized access attempt to view all RaceTime bots by user %s",
                current_user.id if current_user else None,
            )
            return []

        return await self.repository.get_all_bots()

    async def get_active_bots(self) -> list[RacetimeBot]:
        """
        Get all active RaceTime bots.

        No authorization required - this is used by the system to start bots.

        Returns:
            List of active bots
        """
        return await self.repository.get_active_bots()

    async def get_bot_by_id(
        self, bot_id: int, current_user: Optional[User]
    ) -> Optional[RacetimeBot]:
        """
        Get a RaceTime bot by ID.

        Authorization: Only ADMIN and SUPERADMIN can view bot details.

        Args:
            bot_id: Bot ID
            current_user: Current user

        Returns:
            Bot or None if not found/unauthorized
        """
        if not current_user or not self.auth_service.can_access_admin_panel(
            current_user
        ):
            logger.warning(
                "Unauthorized access attempt to view RaceTime bot %s by user %s",
                bot_id,
                current_user.id if current_user else None,
            )
            return None

        return await self.repository.get_bot_by_id(bot_id)

    async def create_bot(
        self,
        category: str,
        client_id: str,
        client_secret: str,
        name: str,
        description: Optional[str],
        is_active: bool,
        current_user: User,
    ) -> Optional[RacetimeBot]:
        """
        Create a new RaceTime bot.

        Authorization: Only ADMIN and SUPERADMIN can create bots.

        Args:
            category: RaceTime category slug
            client_id: OAuth2 client ID
            client_secret: OAuth2 client secret
            name: Friendly name
            description: Optional description
            is_active: Whether bot is active
            current_user: Current user

        Returns:
            Created bot or None if unauthorized
        """
        if not self.auth_service.can_access_admin_panel(current_user):
            logger.warning(
                "Unauthorized attempt to create RaceTime bot by user %s",
                current_user.id,
            )
            return None

        # Check if category already exists
        existing = await self.repository.get_bot_by_category(category)
        if existing:
            logger.warning(
                "Attempted to create duplicate RaceTime bot for category %s",
                category,
            )
            raise ValueError(f"Bot for category '{category}' already exists")

        bot = await self.repository.create_bot(
            category=category,
            client_id=client_id,
            client_secret=client_secret,
            name=name,
            description=description,
            is_active=is_active,
        )

        # Emit event
        await EventBus.emit(
            RacetimeBotCreatedEvent(
                user_id=current_user.id,
                entity_id=bot.id,
                category=category,
                name=name,
            )
        )

        return bot

    async def update_bot(
        self, bot_id: int, current_user: User, **updates
    ) -> Optional[RacetimeBot]:
        """
        Update a RaceTime bot.

        Authorization: Only ADMIN and SUPERADMIN can update bots.

        Args:
            bot_id: Bot ID
            current_user: Current user
            **updates: Fields to update

        Returns:
            Updated bot or None if not found/unauthorized
        """
        if not self.auth_service.can_access_admin_panel(current_user):
            logger.warning(
                "Unauthorized attempt to update RaceTime bot %s by user %s",
                bot_id,
                current_user.id,
            )
            return None

        # If updating category, check for duplicates
        if 'category' in updates:
            existing = await self.repository.get_bot_by_category(updates['category'])
            if existing and existing.id != bot_id:
                raise ValueError(
                    f"Bot for category '{updates['category']}' already exists"
                )

        bot = await self.repository.update_bot(bot_id, **updates)
        if not bot:
            return None

        # Emit event
        await EventBus.emit(
            RacetimeBotUpdatedEvent(
                user_id=current_user.id,
                entity_id=bot_id,
                category=bot.category,
                changed_fields=list(updates.keys()),
            )
        )

        return bot

    async def delete_bot(self, bot_id: int, current_user: User) -> bool:
        """
        Delete a RaceTime bot.

        Authorization: Only SUPERADMIN can delete bots.

        Args:
            bot_id: Bot ID
            current_user: Current user

        Returns:
            True if deleted, False if not found/unauthorized
        """
        if not current_user.has_permission(Permission.SUPERADMIN):
            logger.warning(
                "Unauthorized attempt to delete RaceTime bot %s by user %s",
                bot_id,
                current_user.id,
            )
            return False

        bot = await self.repository.get_bot_by_id(bot_id)
        if not bot:
            return False

        category = bot.category
        deleted = await self.repository.delete_bot(bot_id)

        if deleted:
            # Emit event
            await EventBus.emit(
                RacetimeBotDeletedEvent(
                    user_id=current_user.id,
                    entity_id=bot_id,
                    category=category,
                )
            )

        return deleted

    async def get_bots_for_organization(
        self, organization_id: int, current_user: Optional[User]
    ) -> list[RacetimeBot]:
        """
        Get RaceTime bots assigned to an organization.

        Authorization: User must be a member of the organization or an admin.

        Args:
            organization_id: Organization ID
            current_user: Current user

        Returns:
            List of bots assigned to organization (or empty if unauthorized)
        """
        if not current_user:
            return []

        # Check if user has access to this organization
        is_member = await self.org_repository.get_member(organization_id, current_user.id) is not None

        if not is_member and not self.auth_service.can_access_admin_panel(current_user):
            logger.warning(
                "Unauthorized attempt to view RaceTime bots for org %s by user %s",
                organization_id,
                current_user.id,
            )
            return []

        return await self.repository.get_bots_for_organization(organization_id)

    async def assign_bot_to_organization(
        self, bot_id: int, organization_id: int, current_user: User
    ) -> Optional[RacetimeBotOrganization]:
        """
        Assign a RaceTime bot to an organization.

        Authorization: Only ADMIN and SUPERADMIN can assign bots.

        Args:
            bot_id: Bot ID
            organization_id: Organization ID
            current_user: Current user

        Returns:
            Assignment or None if unauthorized
        """
        if not self.auth_service.can_access_admin_panel(current_user):
            logger.warning(
                "Unauthorized attempt to assign bot %s to org %s by user %s",
                bot_id,
                organization_id,
                current_user.id,
            )
            return None

        return await self.repository.assign_bot_to_organization(
            bot_id, organization_id
        )

    async def unassign_bot_from_organization(
        self, bot_id: int, organization_id: int, current_user: User
    ) -> bool:
        """
        Remove a RaceTime bot assignment from an organization.

        Authorization: Only ADMIN and SUPERADMIN can unassign bots.

        Args:
            bot_id: Bot ID
            organization_id: Organization ID
            current_user: Current user

        Returns:
            True if unassigned, False if not found/unauthorized
        """
        if not self.auth_service.can_access_admin_panel(current_user):
            logger.warning(
                "Unauthorized attempt to unassign bot %s from org %s by user %s",
                bot_id,
                organization_id,
                current_user.id,
            )
            return False

        return await self.repository.unassign_bot_from_organization(
            bot_id, organization_id
        )

    async def get_organizations_for_bot(
        self, bot_id: int, current_user: User
    ) -> list[Organization]:
        """
        Get organizations assigned to a RaceTime bot.

        Authorization: Only ADMIN and SUPERADMIN can view assignments.

        Args:
            bot_id: Bot ID
            current_user: Current user

        Returns:
            List of organizations (or empty if unauthorized)
        """
        if not self.auth_service.can_access_admin_panel(current_user):
            logger.warning(
                "Unauthorized attempt to view orgs for bot %s by user %s",
                bot_id,
                current_user.id,
            )
            return []

        return await self.repository.get_organizations_for_bot(bot_id)
