"""Organization invite models."""

from __future__ import annotations
from tortoise import fields
from tortoise.models import Model


class OrganizationInvite(Model):
    """Invite link for joining an organization."""
    
    id = fields.IntField(pk=True)
    organization = fields.ForeignKeyField('models.Organization', related_name='invites')
    slug = fields.CharField(max_length=100, unique=True, index=True)
    created_by = fields.ForeignKeyField('models.User', related_name='created_invites')
    is_active = fields.BooleanField(default=True)
    max_uses = fields.IntField(null=True)  # None = unlimited
    uses_count = fields.IntField(default=0)
    expires_at = fields.DatetimeField(null=True)
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)
