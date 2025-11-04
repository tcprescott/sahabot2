"""
Race Room Profile model.

Stores reusable RaceTime room configuration profiles that can be assigned to tournaments.
"""

from __future__ import annotations
from tortoise import fields
from tortoise.models import Model


class RaceRoomProfile(Model):
    """Reusable configuration profile for RaceTime race rooms."""

    id = fields.IntField(pk=True)
    organization = fields.ForeignKeyField('models.Organization', related_name='race_room_profiles')
    name = fields.CharField(max_length=255)
    description = fields.TextField(null=True)
    
    # Race timing settings
    start_delay = fields.IntField(default=15)  # Countdown seconds before race starts
    time_limit = fields.IntField(default=24)  # Time limit in hours
    
    # Stream & automation settings
    streaming_required = fields.BooleanField(default=False)  # Require streaming
    auto_start = fields.BooleanField(default=True)  # Auto-start when ready
    
    # Comment settings
    allow_comments = fields.BooleanField(default=True)  # Allow race comments
    hide_comments = fields.BooleanField(default=False)  # Hide comments until race ends
    
    # Chat permissions
    allow_prerace_chat = fields.BooleanField(default=True)  # Chat before race
    allow_midrace_chat = fields.BooleanField(default=True)  # Chat during race
    allow_non_entrant_chat = fields.BooleanField(default=True)  # Non-racers can chat
    
    # Metadata
    is_default = fields.BooleanField(default=False)  # Default profile for organization
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)
    
    # Reverse relations
    tournaments: fields.ReverseRelation["Tournament"]

    class Meta:
        table = "race_room_profiles"
        unique_together = (("organization", "name"),)  # Unique profile names per org

    def __str__(self):
        return f"{self.name} ({self.organization.name if hasattr(self, 'organization') else 'Unknown Org'})"
