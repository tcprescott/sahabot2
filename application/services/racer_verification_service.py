"""
Racer verification service.

Business logic for racer verification system allowing organization admins
to configure Discord roles granted based on RaceTime race completion requirements.
"""

import logging
from datetime import datetime, timezone
from typing import Optional
from models import User, RacerVerification, UserRacerVerification
from application.repositories.racer_verification_repository import (
    RacerVerificationRepository,
    UserRacerVerificationRepository,
)
from application.repositories.organization_repository import OrganizationRepository
from application.services.authorization_service import AuthorizationService
from application.services.racetime_api_service import RacetimeApiService
from application.services.audit_service import AuditService
from discordbot.client import get_bot_instance

logger = logging.getLogger(__name__)


class RacerVerificationService:
    """Business logic for racer verification system."""

    def __init__(self):
        self.repository = RacerVerificationRepository()
        self.user_verification_repository = UserRacerVerificationRepository()
        self.org_repository = OrganizationRepository()
        self.auth_service = AuthorizationService()
        self.racetime_api = RacetimeApiService()
        self.audit = AuditService()

    async def create_verification(
        self,
        current_user: User,
        organization_id: int,
        guild_id: int,
        role_id: int,
        role_name: str,
        categories: list[str],
        minimum_races: int = 5,
        count_forfeits: bool = False,
        count_dq: bool = False,
    ) -> Optional[RacerVerification]:
        """
        Create racer verification configuration.

        Args:
            current_user: User creating the configuration
            organization_id: Organization ID
            guild_id: Discord guild ID
            role_id: Discord role ID to grant
            role_name: Discord role name
            categories: List of RaceTime categories to count races from
            minimum_races: Minimum races required (across all categories)
            count_forfeits: Whether to count forfeited races
            count_dq: Whether to count disqualified races

        Returns:
            Created RacerVerification or None if unauthorized
        """
        # Check permissions
        if not await self.auth_service.can_manage_org_members(
            current_user,
            organization_id
        ):
            logger.warning(
                "User %s attempted to create racer verification for org %s without permission",
                current_user.id,
                organization_id
            )
            return None

        # Create verification
        verification = await self.repository.create(
            organization_id=organization_id,
            guild_id=guild_id,
            role_id=role_id,
            role_name=role_name,
            categories=categories,
            minimum_races=minimum_races,
            count_forfeits=count_forfeits,
            count_dq=count_dq,
        )

        # Audit log
        await self.audit.log_action(
            user=current_user,
            action="racer_verification_created",
            details={
                "verification_id": verification.id,
                "organization_id": organization_id,
                "categories": categories,
                "minimum_races": minimum_races,
            }
        )

        logger.info(
            "Created racer verification %s for org %s by user %s",
            verification.id,
            organization_id,
            current_user.id
        )

        return verification

    async def get_verifications_for_organization(
        self,
        current_user: User,
        organization_id: int
    ) -> list[RacerVerification]:
        """
        Get all racer verifications for an organization.

        Args:
            current_user: Current user
            organization_id: Organization ID

        Returns:
            List of RacerVerification instances (empty if unauthorized)
        """
        # Check membership
        member = await self.org_repository.get_member(organization_id, current_user.id)
        if not member:
            logger.warning(
                "User %s attempted to view racer verifications for org %s without membership",
                current_user.id,
                organization_id
            )
            return []

        return await self.repository.list_by_organization(organization_id)

    async def update_verification(
        self,
        current_user: User,
        verification_id: int,
        **updates
    ) -> Optional[RacerVerification]:
        """
        Update racer verification configuration.

        Args:
            current_user: User updating the configuration
            verification_id: RacerVerification ID
            **updates: Fields to update

        Returns:
            Updated RacerVerification or None if unauthorized/not found
        """
        # Get verification
        verification = await self.repository.get_by_id(verification_id)
        if not verification:
            return None

        # Check permissions
        if not await self.auth_service.can_manage_org_members(
            current_user,
            verification.organization_id
        ):
            logger.warning(
                "User %s attempted to update racer verification %s without permission",
                current_user.id,
                verification_id
            )
            return None

        # Update
        updated_verification = await self.repository.update(verification_id, **updates)

        # Audit log
        await self.audit.log_action(
            user=current_user,
            action="racer_verification_updated",
            details={
                "verification_id": verification_id,
                "updated_fields": list(updates.keys()),
            }
        )

        return updated_verification

    async def delete_verification(
        self,
        current_user: User,
        verification_id: int
    ) -> bool:
        """
        Delete racer verification configuration.

        Args:
            current_user: User deleting the configuration
            verification_id: RacerVerification ID

        Returns:
            True if deleted, False if unauthorized/not found
        """
        # Get verification
        verification = await self.repository.get_by_id(verification_id)
        if not verification:
            return False

        # Check permissions
        if not await self.auth_service.can_manage_org_members(
            current_user,
            verification.organization_id
        ):
            logger.warning(
                "User %s attempted to delete racer verification %s without permission",
                current_user.id,
                verification_id
            )
            return False

        # Delete
        result = await self.repository.delete(verification_id)

        if result:
            # Audit log
            await self.audit.log_action(
                user=current_user,
                action="racer_verification_deleted",
                details={"verification_id": verification_id}
            )

        return result

    async def check_user_eligibility(
        self,
        user: User,
        verification_id: int
    ) -> dict:
        """
        Check if a user is eligible for racer verification.

        Args:
            user: User to check
            verification_id: RacerVerification ID

        Returns:
            Dictionary with eligibility details:
            - is_eligible: bool
            - race_count: int
            - minimum_required: int
            - has_racetime_account: bool
            - error: Optional str
        """
        # Get verification config
        verification = await self.repository.get_by_id(verification_id)
        if not verification:
            return {
                "is_eligible": False,
                "race_count": 0,
                "minimum_required": 0,
                "has_racetime_account": False,
                "error": "Verification configuration not found"
            }

        # Check if user has linked RaceTime account
        if not user.racetime_id:
            return {
                "is_eligible": False,
                "race_count": 0,
                "minimum_required": verification.minimum_races,
                "has_racetime_account": False,
                "error": "No RaceTime account linked"
            }

        # Fetch race data from RaceTime.gg (from all categories)
        try:
            all_races = []
            for category in verification.categories:
                races = await self.racetime_api.get_user_races(
                    user=user,
                    category=category,
                    show_entrants=False
                )
                all_races.extend(races)

            # Count qualifying races
            qualifying_races = 0
            for race in all_races:
                # Get user's entrant data from the race
                entrant = next(
                    (e for e in race.get('entrants', []) if e.get('user', {}).get('id') == user.racetime_id),
                    None
                )

                if not entrant:
                    continue

                status = entrant.get('status', {}).get('value', '')

                # Count based on configuration
                if status == 'done':
                    qualifying_races += 1
                elif status == 'dnf' and verification.count_forfeits:
                    qualifying_races += 1
                elif status == 'dq' and verification.count_dq:
                    qualifying_races += 1

            is_eligible = qualifying_races >= verification.minimum_races

            return {
                "is_eligible": is_eligible,
                "race_count": qualifying_races,
                "minimum_required": verification.minimum_races,
                "has_racetime_account": True,
                "error": None
            }

        except Exception as e:
            logger.error(
                "Error checking race eligibility for user %s: %s",
                user.id,
                e,
                exc_info=True
            )
            return {
                "is_eligible": False,
                "race_count": 0,
                "minimum_required": verification.minimum_races,
                "has_racetime_account": True,
                "error": f"Error fetching race data: {str(e)}"
            }

    async def verify_user(
        self,
        user: User,
        verification_id: int
    ) -> Optional[UserRacerVerification]:
        """
        Verify a user and grant Discord role if eligible.

        Args:
            user: User to verify
            verification_id: RacerVerification ID

        Returns:
            UserRacerVerification instance or None if not eligible
        """
        # Check eligibility
        eligibility = await self.check_user_eligibility(user, verification_id)

        if not eligibility["is_eligible"]:
            logger.info(
                "User %s is not eligible for verification %s: %s",
                user.id,
                verification_id,
                eligibility.get("error", "insufficient races")
            )
            return None

        # Get verification config
        verification = await self.repository.get_by_id(verification_id)
        if not verification:
            return None

        # Get or create user verification record
        user_verification = await self.user_verification_repository.get_by_verification_and_user(
            verification_id=verification_id,
            user_id=user.id
        )

        if not user_verification:
            user_verification = await self.user_verification_repository.create(
                verification_id=verification_id,
                user_id=user.id,
                is_verified=True,
                race_count=eligibility["race_count"]
            )
        else:
            # Update existing record
            user_verification = await self.user_verification_repository.update(
                user_verification.id,
                is_verified=True,
                verified_at=datetime.now(timezone.utc),
                race_count=eligibility["race_count"],
                last_checked_at=datetime.now(timezone.utc),
            )

        # Grant Discord role
        role_granted = await self._grant_discord_role(
            user=user,
            guild_id=verification.guild_id,
            role_id=verification.role_id
        )

        if role_granted:
            await self.user_verification_repository.update(
                user_verification.id,
                role_granted=True,
                role_granted_at=datetime.now(timezone.utc),
            )

        # Audit log
        await self.audit.log_action(
            user=user,
            action="racer_verified",
            details={
                "verification_id": verification_id,
                "race_count": eligibility["race_count"],
                "role_granted": role_granted,
            }
        )

        logger.info(
            "User %s verified for verification %s with %d races (role granted: %s)",
            user.id,
            verification_id,
            eligibility["race_count"],
            role_granted
        )

        return user_verification

    async def _grant_discord_role(
        self,
        user: User,
        guild_id: int,
        role_id: int
    ) -> bool:
        """
        Grant Discord role to user.

        Args:
            user: User to grant role to
            guild_id: Discord guild ID
            role_id: Discord role ID

        Returns:
            True if role granted successfully, False otherwise
        """
        try:
            # Get Discord bot instance
            bot = get_bot_instance()
            if not bot:
                logger.warning("Discord bot not available, cannot grant role")
                return False

            # Get guild
            guild = bot.get_guild(guild_id)
            if not guild:
                logger.warning("Guild %s not found, cannot grant role", guild_id)
                return False

            # Get member
            member = guild.get_member(user.discord_id)
            if not member:
                logger.warning(
                    "User %s (discord_id=%s) not found in guild %s",
                    user.id,
                    user.discord_id,
                    guild_id
                )
                return False

            # Get role
            role = guild.get_role(role_id)
            if not role:
                logger.warning("Role %s not found in guild %s", role_id, guild_id)
                return False

            # Grant role
            await member.add_roles(role, reason="Racer verification completed")
            logger.info(
                "Granted role %s to user %s in guild %s",
                role.name,
                user.discord_username,
                guild.name
            )
            return True

        except Exception as e:
            logger.error(
                "Error granting Discord role to user %s: %s",
                user.id,
                e,
                exc_info=True
            )
            return False

    async def get_user_verification_status(
        self,
        user: User,
        verification_id: int
    ) -> Optional[UserRacerVerification]:
        """
        Get user's verification status.

        Args:
            user: User to check
            verification_id: RacerVerification ID

        Returns:
            UserRacerVerification instance or None if not found
        """
        return await self.user_verification_repository.get_by_verification_and_user(
            verification_id=verification_id,
            user_id=user.id
        )
