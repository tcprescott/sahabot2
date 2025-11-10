"""
Feature flag service for business logic.
"""

import logging
from typing import Optional

from models import User, OrganizationFeatureFlag, Permission, FeatureFlag
from application.repositories.feature_flag_repository import FeatureFlagRepository
from application.services.core.audit_service import AuditService

logger = logging.getLogger(__name__)


class FeatureFlagService:
    """Business logic for feature flag management."""

    # Feature flag descriptions
    DESCRIPTIONS = {
        FeatureFlag.LIVE_RACES: "Live race monitoring and management",
        FeatureFlag.ADVANCED_PRESETS: "Advanced randomizer preset management",
        FeatureFlag.RACETIME_BOT: "RaceTime.gg bot integration",
        FeatureFlag.SCHEDULED_TASKS: "Scheduled task automation",
        FeatureFlag.DISCORD_EVENTS: "Discord scheduled event integration",
    }

    def __init__(self):
        self.repository = FeatureFlagRepository()
        self.audit_service = AuditService()

    async def is_feature_enabled(
        self, organization_id: int, feature_key: FeatureFlag
    ) -> bool:
        """
        Check if a feature is enabled for an organization.

        Args:
            organization_id: Organization ID
            feature_key: Feature flag enum

        Returns:
            True if enabled, False otherwise
        """
        return await self.repository.is_feature_enabled(organization_id, feature_key)

    async def get_organization_features(
        self, organization_id: int, current_user: User
    ) -> list[OrganizationFeatureFlag]:
        """
        Get all feature flags for an organization.

        Args:
            organization_id: Organization ID
            current_user: Current user

        Returns:
            List of feature flags (empty if unauthorized)
        """
        # Only SUPERADMIN can view feature flags
        if not current_user.has_permission(Permission.SUPERADMIN):
            logger.warning(
                "User %s attempted to view feature flags for org %s without SUPERADMIN",
                current_user.id,
                organization_id,
            )
            return []

        return await self.repository.list_by_organization(organization_id)

    async def get_enabled_features(self, organization_id: int) -> list[FeatureFlag]:
        """
        Get list of enabled feature flags for an organization.

        This method doesn't require authorization - it's for internal feature checks.

        Args:
            organization_id: Organization ID

        Returns:
            List of enabled feature flag enums
        """
        flags = await self.repository.list_enabled_by_organization(organization_id)
        return [flag.feature_key for flag in flags]

    async def enable_feature(
        self,
        organization_id: int,
        feature_key: FeatureFlag,
        current_user: User,
        notes: Optional[str] = None,
    ) -> Optional[OrganizationFeatureFlag]:
        """
        Enable a feature for an organization.

        Args:
            organization_id: Organization ID
            feature_key: Feature flag enum
            current_user: User enabling the feature
            notes: Optional notes

        Returns:
            Feature flag if successful, None if unauthorized
        """
        # Only SUPERADMIN can enable features
        if not current_user.has_permission(Permission.SUPERADMIN):
            logger.warning(
                "User %s attempted to enable feature %s for org %s without SUPERADMIN",
                current_user.id,
                feature_key,
                organization_id,
            )
            return None

        # Check if flag already exists
        existing = await self.repository.get_by_org_and_key(
            organization_id, feature_key
        )

        if existing:
            # Update existing flag
            flag = await self.repository.update(
                flag_id=existing.id,
                enabled=True,
                enabled_by_id=current_user.id,
                notes=notes,
            )
        else:
            # Create new flag
            flag = await self.repository.create(
                organization_id=organization_id,
                feature_key=feature_key,
                enabled=True,
                enabled_by_id=current_user.id,
                notes=notes,
            )

        # Audit log
        await self.audit_service.log_action(
            user=current_user,
            action="feature_flag_enabled",
            details={
                "organization_id": organization_id,
                "feature_key": feature_key,
                "notes": notes,
            },
        )

        logger.info(
            "User %s enabled feature %s for organization %s",
            current_user.id,
            feature_key,
            organization_id,
        )

        return flag

    async def disable_feature(
        self,
        organization_id: int,
        feature_key: FeatureFlag,
        current_user: User,
        notes: Optional[str] = None,
    ) -> Optional[OrganizationFeatureFlag]:
        """
        Disable a feature for an organization.

        Args:
            organization_id: Organization ID
            feature_key: Feature flag enum
            current_user: User disabling the feature
            notes: Optional notes

        Returns:
            Feature flag if successful, None if unauthorized or not found
        """
        # Only SUPERADMIN can disable features
        if not current_user.has_permission(Permission.SUPERADMIN):
            logger.warning(
                "User %s attempted to disable feature %s for org %s without SUPERADMIN",
                current_user.id,
                feature_key,
                organization_id,
            )
            return None

        # Get existing flag
        existing = await self.repository.get_by_org_and_key(
            organization_id, feature_key
        )
        if not existing:
            logger.warning(
                "User %s attempted to disable non-existent feature %s for org %s",
                current_user.id,
                feature_key,
                organization_id,
            )
            return None

        # Update flag
        flag = await self.repository.update(
            flag_id=existing.id, enabled=False, notes=notes
        )

        # Audit log
        await self.audit_service.log_action(
            user=current_user,
            action="feature_flag_disabled",
            details={
                "organization_id": organization_id,
                "feature_key": feature_key,
                "notes": notes,
            },
        )

        logger.info(
            "User %s disabled feature %s for organization %s",
            current_user.id,
            feature_key,
            organization_id,
        )

        return flag

    async def toggle_feature(
        self,
        organization_id: int,
        feature_key: FeatureFlag,
        current_user: User,
        notes: Optional[str] = None,
    ) -> Optional[OrganizationFeatureFlag]:
        """
        Toggle a feature for an organization (enable if disabled, disable if enabled).

        Args:
            organization_id: Organization ID
            feature_key: Feature flag enum
            current_user: User toggling the feature
            notes: Optional notes

        Returns:
            Feature flag if successful, None if unauthorized
        """
        # Only SUPERADMIN can toggle features
        if not current_user.has_permission(Permission.SUPERADMIN):
            logger.warning(
                "User %s attempted to toggle feature %s for org %s without SUPERADMIN",
                current_user.id,
                feature_key,
                organization_id,
            )
            return None

        # Check current state
        existing = await self.repository.get_by_org_and_key(
            organization_id, feature_key
        )

        if existing and existing.enabled:
            # Disable
            return await self.disable_feature(
                organization_id, feature_key, current_user, notes
            )
        else:
            # Enable
            return await self.enable_feature(
                organization_id, feature_key, current_user, notes
            )

    async def get_all_feature_keys(self) -> list[dict]:
        """
        Get all available feature keys with descriptions.

        Returns:
            List of dicts with 'key' and 'description'
        """
        return [
            {"key": flag, "description": self.DESCRIPTIONS.get(flag, "Unknown feature")}
            for flag in FeatureFlag
        ]

    async def get_organizations_with_feature(
        self, feature_key: FeatureFlag, current_user: User
    ) -> list[OrganizationFeatureFlag]:
        """
        Get all organizations that have a specific feature enabled.

        Args:
            feature_key: Feature flag enum
            current_user: Current user

        Returns:
            List of feature flags (empty if unauthorized)
        """
        # Only SUPERADMIN can view this
        if not current_user.has_permission(Permission.SUPERADMIN):
            logger.warning(
                "User %s attempted to view orgs with feature %s without SUPERADMIN",
                current_user.id,
                feature_key,
            )
            return []

        return await self.repository.list_by_feature_key(feature_key)
