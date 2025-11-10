"""
Builtin Task Override model for SahaBot2.

This module defines the database model for overriding built-in task settings,
specifically for enabling/disabling built-in tasks that are defined in code.
"""

from tortoise import fields
from tortoise.models import Model


class BuiltinTaskOverride(Model):
    """
    Builtin task override model.

    Stores overrides for built-in tasks that are defined in code.
    Currently only supports enabling/disabling tasks, but can be extended
    for other overridable settings in the future.
    """

    id = fields.IntField(pk=True)
    task_id = fields.CharField(max_length=255, unique=True, index=True)
    is_active = fields.BooleanField()

    # Metadata
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    class Meta:
        table = "builtin_task_overrides"
