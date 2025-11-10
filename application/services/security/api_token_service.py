"""Service for API token management and verification."""

from __future__ import annotations

import hashlib
import secrets
import logging
from datetime import datetime
from typing import Optional, Tuple

from models import User
from models.api_token import ApiToken
from application.repositories.api_token_repository import ApiTokenRepository

logger = logging.getLogger(__name__)


def _hash_token(token: str) -> str:
    """
    Hash a token using SHA256.

    Note: The token lookup is performed by the database using an indexed query,
    so timing attacks are not a concern. The hash comparison happens at the
    database level, not in application code.

    Args:
        token: Plaintext token to hash

    Returns:
        str: Hex-encoded hash of the token
    """
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


class ApiTokenService:
    """Business logic for API tokens."""

    def __init__(self) -> None:
        self.repo = ApiTokenRepository()

    async def generate_token(
        self,
        user: User,
        name: Optional[str] = None,
        expires_at: Optional[datetime] = None,
    ) -> Tuple[str, ApiToken]:
        """
        Generate a new token for a user and persist its hash.

        Returns the plaintext token and the token model.
        """
        # 32 bytes ~ 43 chars URL-safe
        token = secrets.token_urlsafe(32)
        token_hash = _hash_token(token)
        api_token = await self.repo.create(
            user_id=user.id, token_hash=token_hash, name=name, expires_at=expires_at
        )
        logger.info("Created API token %s for user %s", api_token.id, user.id)
        return token, api_token

    async def verify_token(self, token: str) -> Optional[User]:
        """Verify a plaintext token and return the associated user if valid."""
        token_hash = _hash_token(token)
        api_token: Optional[ApiToken] = await self.repo.get_by_hash(token_hash)
        if not api_token:
            return None
        if not api_token.is_valid():
            return None
        await self.repo.touch_last_used(api_token)
        return await api_token.user

    async def list_user_tokens(self, user_id: int) -> list[ApiToken]:
        """List all tokens for a user."""
        return await self.repo.list_by_user(user_id)

    async def create_token(
        self, user_id: int, name: str, expires_at: Optional[datetime] = None
    ) -> dict:
        """Create a new token and return it with the plaintext token."""
        user = await User.get_or_none(id=user_id)
        if not user:
            raise ValueError("User not found")

        token, api_token = await self.generate_token(user, name, expires_at)
        return {"token": token, "api_token": api_token}

    async def revoke_token(self, token_id: int) -> None:
        """Revoke a token by ID."""
        token = await self.repo.get_by_id(token_id)
        if not token:
            raise ValueError("Token not found")
        await self.repo.revoke(token)
