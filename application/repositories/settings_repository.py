"""
Settings repository providing data access for GlobalSetting and OrganizationSetting.
"""

from __future__ import annotations
from typing import Optional
from models import GlobalSetting, OrganizationSetting


class SettingsRepository:
    """Repository for settings access and persistence."""

    # Global settings
    async def list_global(self) -> list[GlobalSetting]:
        return await GlobalSetting.all().order_by("key")

    async def get_global(self, key: str) -> Optional[GlobalSetting]:
        return await GlobalSetting.get_or_none(key=key)

    async def set_global(
        self,
        key: str,
        value: str,
        description: Optional[str] = None,
        is_public: bool = False,
    ) -> GlobalSetting:
        existing = await self.get_global(key)
        if existing:
            existing.value = value
            if description is not None:
                existing.description = description
            existing.is_public = (
                is_public if is_public is not None else existing.is_public
            )
            await existing.save()
            return existing
        return await GlobalSetting.create(
            key=key, value=value, description=description, is_public=is_public
        )

    async def delete_global(self, key: str) -> int:
        return await GlobalSetting.filter(key=key).delete()

    # Organization settings
    async def list_org(self, organization_id: int) -> list[OrganizationSetting]:
        return await OrganizationSetting.filter(
            organization_id=organization_id
        ).order_by("key")

    async def get_org(
        self, organization_id: int, key: str
    ) -> Optional[OrganizationSetting]:
        return await OrganizationSetting.get_or_none(
            organization_id=organization_id, key=key
        )

    async def set_org(
        self,
        organization_id: int,
        key: str,
        value: str,
        description: Optional[str] = None,
    ) -> OrganizationSetting:
        existing = await self.get_org(organization_id, key)
        if existing:
            existing.value = value
            if description is not None:
                existing.description = description
            await existing.save()
            return existing
        return await OrganizationSetting.create(
            organization_id=organization_id,
            key=key,
            value=value,
            description=description,
        )

    async def delete_org(self, organization_id: int, key: str) -> int:
        return await OrganizationSetting.filter(
            organization_id=organization_id, key=key
        ).delete()
