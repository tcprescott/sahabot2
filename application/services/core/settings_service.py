"""
Settings service encapsulating business logic for global and organization-specific settings.
"""

from __future__ import annotations
from typing import Optional
from application.repositories.settings_repository import SettingsRepository


class SettingsService:
    """Business logic for settings with fallback and validation hooks."""

    def __init__(self) -> None:
        self.repo = SettingsRepository()

    # Global
    async def list_global(self) -> list:
        return await self.repo.list_global()

    async def get_global(self, key: str) -> Optional[dict]:
        item = await self.repo.get_global(key)
        if not item:
            return None
        return {"key": item.key, "value": item.value, "description": item.description, "is_public": item.is_public}

    async def set_global(self, key: str, value: str, description: Optional[str] = None, is_public: bool = False) -> None:
        # Hook for validation/normalization per key can be added here
        await self.repo.set_global(key=key, value=value, description=description, is_public=is_public)

    async def delete_global(self, key: str) -> None:
        await self.repo.delete_global(key)

    # Organization
    async def list_org(self, organization_id: int) -> list:
        return await self.repo.list_org(organization_id)

    async def get_org(self, organization_id: int, key: str) -> Optional[dict]:
        item = await self.repo.get_org(organization_id, key)
        if not item:
            return None
        return {"key": item.key, "value": item.value, "description": item.description}

    async def set_org(self, organization_id: int, key: str, value: str, description: Optional[str] = None) -> None:
        # Hook for per-org validation can be added here
        await self.repo.set_org(organization_id=organization_id, key=key, value=value, description=description)

    async def delete_org(self, organization_id: int, key: str) -> None:
        await self.repo.delete_org(organization_id=organization_id, key=key)

    async def get_effective(self, key: str, organization_id: Optional[int] = None) -> Optional[str]:
        """Get effective value: org override first, then global setting."""
        if organization_id is not None:
            org_item = await self.repo.get_org(organization_id, key)
            if org_item:
                return org_item.value
        glob_item = await self.repo.get_global(key)
        return glob_item.value if glob_item else None
