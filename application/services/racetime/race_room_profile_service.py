"""
Race room profile service.

Business logic for race room profile management.
"""

import logging
from typing import Optional
from models import User, RaceRoomProfile
from application.repositories.race_room_profile_repository import (
    RaceRoomProfileRepository,
)
from application.services.organizations.organization_service import OrganizationService
from application.services.authorization.authorization_service_v2 import (
    AuthorizationServiceV2,
)
from application.events import EventBus, PresetCreatedEvent, PresetUpdatedEvent

logger = logging.getLogger(__name__)


class RaceRoomProfileService:
    """Service for race room profile business logic."""

    def __init__(self):
        self.repository = RaceRoomProfileRepository()
        self.org_service = OrganizationService()
        self.auth = AuthorizationServiceV2()

    async def get_profile(
        self, current_user: User, organization_id: int, profile_id: int
    ) -> Optional[RaceRoomProfile]:
        """
        Get a race room profile.

        Args:
            current_user: Current user
            organization_id: Organization ID
            profile_id: Profile ID

        Returns:
            Profile if found and user has access, None otherwise
        """
        # Check membership via get_member
        member = await self.org_service.get_member(organization_id, current_user.id)
        if not member:
            logger.warning(
                "User %s attempted to access profile %s in organization %s without membership",
                current_user.id,
                profile_id,
                organization_id,
            )
            return None

        return await self.repository.get_for_org(organization_id, profile_id)

    async def list_profiles(
        self, current_user: User, organization_id: int
    ) -> list[RaceRoomProfile]:
        """
        List all race room profiles for an organization.

        Args:
            current_user: Current user
            organization_id: Organization ID

        Returns:
            List of profiles (empty if user lacks access)
        """
        # Check membership via get_member
        member = await self.org_service.get_member(organization_id, current_user.id)
        if not member:
            logger.warning(
                "User %s attempted to list profiles in organization %s without membership",
                current_user.id,
                organization_id,
            )
            return []

        return await self.repository.list_for_org(organization_id)

    async def get_default_profile(
        self, current_user: User, organization_id: int
    ) -> Optional[RaceRoomProfile]:
        """
        Get the default race room profile for an organization.

        Args:
            current_user: Current user
            organization_id: Organization ID

        Returns:
            Default profile if exists and user has access, None otherwise
        """
        # Check membership via get_member
        member = await self.org_service.get_member(organization_id, current_user.id)
        if not member:
            logger.warning(
                "User %s attempted to get default profile in organization %s without membership",
                current_user.id,
                organization_id,
            )
            return None

        return await self.repository.get_default_for_org(organization_id)

    async def create_profile(
        self,
        current_user: User,
        organization_id: int,
        name: str,
        description: str = "",
        start_delay: int = 15,
        time_limit: int = 24,
        streaming_required: bool = False,
        auto_start: bool = True,
        allow_comments: bool = True,
        hide_comments: bool = False,
        allow_prerace_chat: bool = True,
        allow_midrace_chat: bool = True,
        allow_non_entrant_chat: bool = True,
        is_default: bool = False,
    ) -> Optional[RaceRoomProfile]:
        """
        Create a new race room profile.

        Args:
            current_user: Current user
            organization_id: Organization ID
            name: Profile name
            description: Profile description
            start_delay: Race start delay in seconds
            time_limit: Race time limit in hours
            streaming_required: Whether streaming is required
            auto_start: Whether to auto-start races
            allow_comments: Whether to allow comments
            hide_comments: Whether to hide comments
            allow_prerace_chat: Whether to allow pre-race chat
            allow_midrace_chat: Whether to allow mid-race chat
            allow_non_entrant_chat: Whether to allow non-entrant chat
            is_default: Whether this is the default profile

        Returns:
            Created profile if authorized, None otherwise
        """
        # Check permission
        if not current_user:
            logger.warning(
                "Unauthenticated create profile attempt for org %s", organization_id
            )
            return None

        can_manage = await self.auth.can(
            current_user,
            action=self.auth.get_action_for_operation("race_room_profile", "create"),
            resource=self.auth.get_resource_identifier("race_room_profile", "*"),
            organization_id=organization_id,
        )
        if not can_manage:
            logger.warning(
                "User %s attempted to create profile in organization %s without permission",
                current_user.id,
                organization_id,
            )
            return None

        profile = await self.repository.create(
            organization_id=organization_id,
            name=name,
            description=description,
            start_delay=start_delay,
            time_limit=time_limit,
            streaming_required=streaming_required,
            auto_start=auto_start,
            allow_comments=allow_comments,
            hide_comments=hide_comments,
            allow_prerace_chat=allow_prerace_chat,
            allow_midrace_chat=allow_midrace_chat,
            allow_non_entrant_chat=allow_non_entrant_chat,
            is_default=is_default,
        )

        # Emit event
        await EventBus.emit(
            PresetCreatedEvent(
                user_id=current_user.id,
                organization_id=organization_id,
                entity_id=profile.id,
                preset_name=name,
            )
        )

        return profile

    async def update_profile(
        self,
        current_user: User,
        organization_id: int,
        profile_id: int,
        **updates,
    ) -> Optional[RaceRoomProfile]:
        """
        Update a race room profile.

        Args:
            current_user: Current user
            organization_id: Organization ID
            profile_id: Profile ID
            **updates: Fields to update

        Returns:
            Updated profile if authorized, None otherwise
        """
        # Check permission
        if not current_user:
            logger.warning(
                "Unauthenticated update profile attempt for org %s", organization_id
            )
            return None

        can_manage = await self.auth.can(
            current_user,
            action=self.auth.get_action_for_operation("race_room_profile", "update"),
            resource=self.auth.get_resource_identifier(
                "race_room_profile", str(profile_id)
            ),
            organization_id=organization_id,
        )
        if not can_manage:
            logger.warning(
                "User %s attempted to update profile %s in organization %s without permission",
                current_user.id,
                profile_id,
                organization_id,
            )
            return None

        profile = await self.repository.update(organization_id, profile_id, **updates)

        if profile:
            # Emit event
            await EventBus.emit(
                PresetUpdatedEvent(
                    user_id=current_user.id,
                    organization_id=organization_id,
                    entity_id=profile.id,
                    preset_name=profile.name,
                    changed_fields=list(updates.keys()),
                )
            )

        return profile

    async def delete_profile(
        self, current_user: User, organization_id: int, profile_id: int
    ) -> bool:
        """
        Delete a race room profile.

        Args:
            current_user: Current user
            organization_id: Organization ID
            profile_id: Profile ID

        Returns:
            True if deleted, False otherwise
        """
        # Check permission
        if not current_user:
            logger.warning(
                "Unauthenticated delete profile attempt for org %s", organization_id
            )
            return False

        can_manage = await self.auth.can(
            current_user,
            action=self.auth.get_action_for_operation("race_room_profile", "delete"),
            resource=self.auth.get_resource_identifier(
                "race_room_profile", str(profile_id)
            ),
            organization_id=organization_id,
        )
        if not can_manage:
            logger.warning(
                "User %s attempted to delete profile %s in organization %s without permission",
                current_user.id,
                profile_id,
                organization_id,
            )
            return False

        return await self.repository.delete(organization_id, profile_id)

    async def set_default_profile(
        self, current_user: User, organization_id: int, profile_id: int
    ) -> bool:
        """
        Set a race room profile as the default for the organization.

        Args:
            current_user: Current user
            organization_id: Organization ID
            profile_id: Profile ID

        Returns:
            True if successful, False otherwise
        """
        # Check permission
        if not current_user:
            logger.warning(
                "Unauthenticated set_default_profile attempt for org %s",
                organization_id,
            )
            return False

        can_manage = await self.auth.can(
            current_user,
            action=self.auth.get_action_for_operation("race_room_profile", "update"),
            resource=self.auth.get_resource_identifier(
                "race_room_profile", str(profile_id)
            ),
            organization_id=organization_id,
        )
        if not can_manage:
            logger.warning(
                "User %s attempted to set default profile %s in organization %s without permission",
                current_user.id,
                profile_id,
                organization_id,
            )
            return False

        return await self.repository.set_as_default(organization_id, profile_id)
