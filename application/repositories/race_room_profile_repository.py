"""
Race room profile repository.

Handles data access for race room profiles.
"""
import logging
from typing import Optional
from models import RaceRoomProfile

logger = logging.getLogger(__name__)


class RaceRoomProfileRepository:
    """Repository for race room profile data access."""

    async def get_by_id(self, profile_id: int) -> Optional[RaceRoomProfile]:
        """
        Get a race room profile by ID.

        Args:
            profile_id: Profile ID

        Returns:
            Profile if found, None otherwise
        """
        return await RaceRoomProfile.filter(id=profile_id).first()

    async def get_for_org(
        self, organization_id: int, profile_id: int
    ) -> Optional[RaceRoomProfile]:
        """
        Get a race room profile by ID within an organization.

        Args:
            organization_id: Organization ID
            profile_id: Profile ID

        Returns:
            Profile if found and belongs to organization, None otherwise
        """
        return await RaceRoomProfile.filter(
            id=profile_id, organization_id=organization_id
        ).first()

    async def list_for_org(self, organization_id: int) -> list[RaceRoomProfile]:
        """
        List all race room profiles for an organization.

        Args:
            organization_id: Organization ID

        Returns:
            List of profiles
        """
        return await RaceRoomProfile.filter(organization_id=organization_id).all()

    async def get_default_for_org(
        self, organization_id: int
    ) -> Optional[RaceRoomProfile]:
        """
        Get the default race room profile for an organization.

        Args:
            organization_id: Organization ID

        Returns:
            Default profile if exists, None otherwise
        """
        return await RaceRoomProfile.filter(
            organization_id=organization_id, is_default=True
        ).first()

    async def create(
        self,
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
    ) -> RaceRoomProfile:
        """
        Create a new race room profile.

        Args:
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
            Created profile
        """
        profile = await RaceRoomProfile.create(
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
        logger.info(
            "Created race room profile %s for organization %s",
            profile.id,
            organization_id,
        )
        return profile

    async def update(
        self, organization_id: int, profile_id: int, **updates
    ) -> Optional[RaceRoomProfile]:
        """
        Update a race room profile.

        Args:
            organization_id: Organization ID
            profile_id: Profile ID
            **updates: Fields to update

        Returns:
            Updated profile if found, None otherwise
        """
        profile = await self.get_for_org(organization_id, profile_id)
        if not profile:
            return None

        await profile.update_from_dict(updates).save()
        logger.info(
            "Updated race room profile %s for organization %s",
            profile_id,
            organization_id,
        )
        return profile

    async def delete(self, organization_id: int, profile_id: int) -> bool:
        """
        Delete a race room profile.

        Args:
            organization_id: Organization ID
            profile_id: Profile ID

        Returns:
            True if deleted, False if not found
        """
        profile = await self.get_for_org(organization_id, profile_id)
        if not profile:
            return False

        await profile.delete()
        logger.info(
            "Deleted race room profile %s from organization %s",
            profile_id,
            organization_id,
        )
        return True

    async def set_as_default(self, organization_id: int, profile_id: int) -> bool:
        """
        Set a race room profile as the default for the organization.

        Unsets any existing default profile first.

        Args:
            organization_id: Organization ID
            profile_id: Profile ID

        Returns:
            True if successful, False if profile not found
        """
        # Verify profile exists and belongs to organization
        profile = await self.get_for_org(organization_id, profile_id)
        if not profile:
            return False

        # Unset any existing default
        await RaceRoomProfile.filter(
            organization_id=organization_id, is_default=True
        ).update(is_default=False)

        # Set new default
        profile.is_default = True
        await profile.save()

        logger.info(
            "Set race room profile %s as default for organization %s",
            profile_id,
            organization_id,
        )
        return True
