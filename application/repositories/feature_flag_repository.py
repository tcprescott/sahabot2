"""
Feature flag repository for data access.
"""

from typing import Optional
from models import OrganizationFeatureFlag, FeatureFlag


class FeatureFlagRepository:
    """Repository for organization feature flag data access."""

    async def get_by_id(self, flag_id: int) -> Optional[OrganizationFeatureFlag]:
        """
        Get feature flag by ID.

        Args:
            flag_id: Feature flag ID

        Returns:
            Feature flag if found, None otherwise
        """
        return await OrganizationFeatureFlag.filter(id=flag_id).first()

    async def get_by_org_and_key(
        self,
        organization_id: int,
        feature_key: FeatureFlag
    ) -> Optional[OrganizationFeatureFlag]:
        """
        Get feature flag by organization and feature key.

        Args:
            organization_id: Organization ID
            feature_key: Feature flag enum

        Returns:
            Feature flag if found, None otherwise
        """
        return await OrganizationFeatureFlag.filter(
            organization_id=organization_id,
            feature_key=feature_key
        ).first()

    async def list_by_organization(
        self,
        organization_id: int
    ) -> list[OrganizationFeatureFlag]:
        """
        List all feature flags for an organization.

        Args:
            organization_id: Organization ID

        Returns:
            List of feature flags
        """
        return await OrganizationFeatureFlag.filter(
            organization_id=organization_id
        ).order_by('feature_key').all()

    async def list_enabled_by_organization(
        self,
        organization_id: int
    ) -> list[OrganizationFeatureFlag]:
        """
        List enabled feature flags for an organization.

        Args:
            organization_id: Organization ID

        Returns:
            List of enabled feature flags
        """
        return await OrganizationFeatureFlag.filter(
            organization_id=organization_id,
            enabled=True
        ).order_by('feature_key').all()

    async def list_by_feature_key(
        self,
        feature_key: FeatureFlag
    ) -> list[OrganizationFeatureFlag]:
        """
        List all organizations with a specific feature flag.

        Args:
            feature_key: Feature flag enum

        Returns:
            List of feature flags
        """
        return await OrganizationFeatureFlag.filter(
            feature_key=feature_key
        ).order_by('organization_id').all()

    async def create(
        self,
        organization_id: int,
        feature_key: str,
        enabled: bool,
        enabled_by_id: Optional[int],
        notes: Optional[str] = None
    ) -> OrganizationFeatureFlag:
        """
        Create a new feature flag.

        Args:
            organization_id: Organization ID
            feature_key: Feature key
            enabled: Whether feature is enabled
            enabled_by_id: User ID who enabled the feature
            notes: Optional notes

        Returns:
            Created feature flag
        """
        from datetime import datetime, timezone

        data = {
            'organization_id': organization_id,
            'feature_key': feature_key,
            'enabled': enabled,
            'notes': notes,
        }

        if enabled:
            data['enabled_at'] = datetime.now(timezone.utc)
            data['enabled_by_id'] = enabled_by_id

        return await OrganizationFeatureFlag.create(**data)

    async def update(
        self,
        flag_id: int,
        enabled: Optional[bool] = None,
        enabled_by_id: Optional[int] = None,
        notes: Optional[str] = None
    ) -> Optional[OrganizationFeatureFlag]:
        """
        Update a feature flag.

        Args:
            flag_id: Feature flag ID
            enabled: Whether feature is enabled
            enabled_by_id: User ID who updated the feature
            notes: Optional notes

        Returns:
            Updated feature flag if found, None otherwise
        """
        from datetime import datetime, timezone

        flag = await self.get_by_id(flag_id)
        if not flag:
            return None

        updates = {}

        if enabled is not None and enabled != flag.enabled:
            updates['enabled'] = enabled
            if enabled:
                updates['enabled_at'] = datetime.now(timezone.utc)
                updates['enabled_by_id'] = enabled_by_id
            else:
                updates['enabled_at'] = None
                updates['enabled_by_id'] = None

        if notes is not None:
            updates['notes'] = notes

        if updates:
            await flag.update_from_dict(updates).save()

        return flag

    async def delete(self, flag_id: int) -> bool:
        """
        Delete a feature flag.

        Args:
            flag_id: Feature flag ID

        Returns:
            True if deleted, False if not found
        """
        flag = await self.get_by_id(flag_id)
        if not flag:
            return False

        await flag.delete()
        return True

    async def is_feature_enabled(
        self,
        organization_id: int,
        feature_key: str
    ) -> bool:
        """
        Check if a feature is enabled for an organization.

        Args:
            organization_id: Organization ID
            feature_key: Feature key

        Returns:
            True if enabled, False otherwise (including if flag doesn't exist)
        """
        flag = await self.get_by_org_and_key(organization_id, feature_key)
        return flag.enabled if flag else False
