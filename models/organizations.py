from __future__ import annotations
from typing import TYPE_CHECKING
from tortoise import fields
from tortoise.models import Model

if TYPE_CHECKING:
    from .match_schedule import Tournament
    from .audit_log import AuditLog

class Organization(Model):
    id = fields.IntField(pk=True)
    name = fields.CharField(max_length=255, unique=True)
    description = fields.TextField(null=True)
    is_active = fields.BooleanField(default=True)
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    # related fields (reverse relations)
    members: fields.ReverseRelation["OrganizationMember"]
    permissions: fields.ReverseRelation["OrganizationPermission"]
    tournaments: fields.ReverseRelation["Tournament"]
    audit_logs: fields.ReverseRelation["AuditLog"]

class OrganizationMember(Model):
    id = fields.IntField(pk=True)
    organization = fields.ForeignKeyField('models.Organization', related_name='members')
    user = fields.ForeignKeyField('models.User', related_name='organizations')
    permissions = fields.ManyToManyField('models.OrganizationPermission', related_name='members')
    joined_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

class OrganizationPermission(Model):
    id = fields.IntField(pk=True)
    organization = fields.ForeignKeyField('models.Organization', related_name='permissions')
    permission_name = fields.CharField(max_length=100)
    description = fields.TextField(null=True)
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    # related fields (reverse relations / m2m)
    members: fields.ManyToManyRelation["OrganizationMember"]