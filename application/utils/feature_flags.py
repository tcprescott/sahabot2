"""
Feature flag utility functions for easy feature checking.

This module provides convenient helper functions for checking feature flags
without needing to instantiate the service every time.
"""

from typing import Optional
from application.services.organizations.feature_flag_service import FeatureFlagService
from models import FeatureFlag


# Singleton service instance
_feature_flag_service: Optional[FeatureFlagService] = None


def get_service() -> FeatureFlagService:
    """Get or create the feature flag service singleton."""
    global _feature_flag_service
    if _feature_flag_service is None:
        _feature_flag_service = FeatureFlagService()
    return _feature_flag_service


async def is_enabled(organization_id: int, feature_key: FeatureFlag) -> bool:
    """
    Quick check if a feature is enabled for an organization.

    Args:
        organization_id: Organization ID
        feature_key: Feature flag enum

    Returns:
        True if enabled, False otherwise

    Example:
        from application.utils.feature_flags import is_enabled
        from models import FeatureFlag

        if await is_enabled(org_id, FeatureFlag.LIVE_RACES):
            # Show live races UI
            pass
    """
    service = get_service()
    return await service.is_feature_enabled(organization_id, feature_key)


async def get_enabled_features(organization_id: int) -> list[FeatureFlag]:
    """
    Get list of enabled feature flags for an organization.

    Args:
        organization_id: Organization ID

    Returns:
        List of enabled feature flag enums

    Example:
        from application.utils.feature_flags import get_enabled_features
        from models import FeatureFlag

        enabled = await get_enabled_features(org_id)
        if FeatureFlag.RACETIME_BOT in enabled:
            # Enable RaceTime bot features
            pass
    """
    service = get_service()
    return await service.get_enabled_features(organization_id)


# Re-export FeatureFlag for convenience
__all__ = ["is_enabled", "get_enabled_features", "FeatureFlag"]
