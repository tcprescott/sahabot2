"""
Racer verification repository.

Data access layer for racer verification configurations and user verification status.
"""

import logging
from typing import Optional
from models import RacerVerification, UserRacerVerification

logger = logging.getLogger(__name__)


class RacerVerificationRepository:
    """Repository for racer verification configuration data access."""

    async def create(
        self,
        organization_id: int,
        guild_id: int,
        role_id: int,
        role_name: str,
        categories: list[str],
        minimum_races: int = 5,
        count_forfeits: bool = False,
        count_dq: bool = False,
    ) -> RacerVerification:
        """
        Create a new racer verification configuration.

        Args:
            organization_id: Organization ID
            guild_id: Discord guild ID
            role_id: Discord role ID to grant
            role_name: Discord role name
            categories: List of RaceTime categories
            minimum_races: Minimum races required (across all categories)
            count_forfeits: Whether to count forfeited races
            count_dq: Whether to count disqualified races

        Returns:
            Created RacerVerification instance
        """
        return await RacerVerification.create(
            organization_id=organization_id,
            guild_id=guild_id,
            role_id=role_id,
            role_name=role_name,
            categories=categories,
            minimum_races=minimum_races,
            count_forfeits=count_forfeits,
            count_dq=count_dq,
        )

    async def get_by_id(self, verification_id: int) -> Optional[RacerVerification]:
        """Get racer verification by ID."""
        return await RacerVerification.filter(id=verification_id).first()

    async def list_by_organization(
        self,
        organization_id: int,
        active_only: bool = True
    ) -> list[RacerVerification]:
        """List all racer verifications for an organization."""
        query = RacerVerification.filter(organization_id=organization_id)
        if active_only:
            query = query.filter(is_active=True)
        return await query.order_by('-created_at').all()

    async def list_by_guild(
        self,
        guild_id: int,
        active_only: bool = True
    ) -> list[RacerVerification]:
        """List all racer verifications for a Discord guild."""
        query = RacerVerification.filter(guild_id=guild_id)
        if active_only:
            query = query.filter(is_active=True)
        return await query.order_by('-created_at').all()

    async def update(
        self,
        verification_id: int,
        **updates
    ) -> Optional[RacerVerification]:
        """Update racer verification."""
        verification = await self.get_by_id(verification_id)
        if not verification:
            return None

        await verification.update_from_dict(updates).save()
        return verification

    async def delete(self, verification_id: int) -> bool:
        """Delete racer verification (soft delete by setting inactive)."""
        verification = await self.get_by_id(verification_id)
        if not verification:
            return False

        verification.is_active = False
        await verification.save()
        return True


class UserRacerVerificationRepository:
    """Repository for user racer verification status data access."""

    async def create(
        self,
        verification_id: int,
        user_id: int,
        is_verified: bool = False,
        race_count: int = 0,
    ) -> UserRacerVerification:
        """
        Create a new user racer verification record.

        Args:
            verification_id: RacerVerification ID
            user_id: User ID
            is_verified: Whether user is verified
            race_count: Number of qualifying races

        Returns:
            Created UserRacerVerification instance
        """
        return await UserRacerVerification.create(
            verification_id=verification_id,
            user_id=user_id,
            is_verified=is_verified,
            race_count=race_count,
        )

    async def get_by_id(self, user_verification_id: int) -> Optional[UserRacerVerification]:
        """Get user racer verification by ID."""
        return await UserRacerVerification.filter(id=user_verification_id).first()

    async def get_by_verification_and_user(
        self,
        verification_id: int,
        user_id: int
    ) -> Optional[UserRacerVerification]:
        """Get user racer verification by verification and user."""
        return await UserRacerVerification.filter(
            verification_id=verification_id,
            user_id=user_id
        ).first()

    async def list_by_verification(
        self,
        verification_id: int,
        verified_only: bool = False
    ) -> list[UserRacerVerification]:
        """List all user verifications for a racer verification."""
        query = UserRacerVerification.filter(verification_id=verification_id)
        if verified_only:
            query = query.filter(is_verified=True)
        return await query.prefetch_related('user').order_by('-verified_at').all()

    async def list_by_user(
        self,
        user_id: int,
        verified_only: bool = False
    ) -> list[UserRacerVerification]:
        """List all verifications for a user."""
        query = UserRacerVerification.filter(user_id=user_id)
        if verified_only:
            query = query.filter(is_verified=True)
        return await query.prefetch_related('verification').order_by('-verified_at').all()

    async def update(
        self,
        user_verification_id: int,
        **updates
    ) -> Optional[UserRacerVerification]:
        """Update user racer verification."""
        user_verification = await self.get_by_id(user_verification_id)
        if not user_verification:
            return None

        await user_verification.update_from_dict(updates).save()
        return user_verification

    async def delete(self, user_verification_id: int) -> bool:
        """Delete user racer verification."""
        user_verification = await self.get_by_id(user_verification_id)
        if not user_verification:
            return False

        await user_verification.delete()
        return True
