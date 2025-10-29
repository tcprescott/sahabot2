"""Repository for API token data access."""

from __future__ import annotations

from typing import Optional
from datetime import datetime
from models.api_token import ApiToken


class ApiTokenRepository:
    """Data access methods for API tokens."""

    async def get_by_hash(self, token_hash: str) -> Optional[ApiToken]:
        return await ApiToken.get_or_none(token_hash=token_hash)

    async def create(self, user_id: int, token_hash: str, name: Optional[str] = None, expires_at: Optional[datetime] = None) -> ApiToken:
        return await ApiToken.create(
            user_id=user_id,
            token_hash=token_hash,
            name=name,
            expires_at=expires_at,
        )

    async def revoke(self, token: ApiToken) -> None:
        token.is_active = False
        await token.save()

    async def touch_last_used(self, token: ApiToken) -> None:
        token.last_used_at = datetime.utcnow()
        await token.save()
