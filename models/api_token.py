"""API token model for token-based authentication."""

from __future__ import annotations

from tortoise import fields
from tortoise.models import Model
from datetime import datetime, timezone


class ApiToken(Model):
    """
    API token associated with a user.

    Stores a hash of the token value; the plaintext token is only shown upon creation.
    """

    id = fields.IntField(pk=True)
    user = fields.ForeignKeyField(
        "models.User", related_name="api_tokens", on_delete=fields.CASCADE
    )
    name = fields.CharField(max_length=100, null=True)
    token_hash = fields.CharField(max_length=64, unique=True, index=True)
    is_active = fields.BooleanField(default=True)
    created_at = fields.DatetimeField(auto_now_add=True)
    last_used_at = fields.DatetimeField(null=True)
    expires_at = fields.DatetimeField(null=True)

    class Meta:
        table = "api_tokens"

    def is_valid(self) -> bool:
        """Return True if token is active and not expired."""
        if not self.is_active:
            return False
        if self.expires_at is None:
            return True
        now = datetime.now(timezone.utc)
        return now < self.expires_at
