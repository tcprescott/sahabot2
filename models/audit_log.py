"""
Audit log model for tracking user actions.

This module contains the AuditLog model for security and compliance logging.
Includes optional organization context for multi-tenant auditing.
"""

from tortoise import fields
from tortoise.models import Model


class AuditLog(Model):
    """
    Audit log for tracking user actions.

    Attributes:
        id: Primary key
        user: Foreign key to User who performed the action
        organization: Optional foreign key to Organization (tenant context)
        action: Action type/name
        details: JSON field with action details
        ip_address: IP address of the user
        created_at: Timestamp of the action
    """

    id = fields.IntField(pk=True)
    user = fields.ForeignKeyField('models.User', related_name='audit_logs', null=True)
    organization = fields.ForeignKeyField('models.Organization', related_name='audit_logs', null=True, index=True)
    action = fields.CharField(max_length=255)
    details = fields.JSONField(null=True)
    ip_address = fields.CharField(max_length=45, null=True)
    created_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "audit_logs"
        ordering = ["-created_at"]

    def __str__(self) -> str:
        """String representation of audit log entry."""
        return f"{self.action} by {self.user} at {self.created_at}"
