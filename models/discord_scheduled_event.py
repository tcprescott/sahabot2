"""
Discord Scheduled Event models for tournament match integration.

This module provides models for tracking Discord's native scheduled events
that are automatically created for tournament matches.
"""
from tortoise import fields
from tortoise.models import Model


class DiscordScheduledEvent(Model):
    """
    Tracks Discord scheduled events linked to tournament matches.

    Discord scheduled events are the native event system in Discord servers
    that appear in the "Events" section. This model maintains the mapping
    between our Match records and Discord's scheduled event IDs.
    """

    id = fields.IntField(pk=True)

    # Discord event ID (Discord's unique identifier for the scheduled event)
    scheduled_event_id = fields.BigIntField(unique=True, index=True)

    # Match and organization relationships
    match = fields.ForeignKeyField('models.Match', related_name='discord_events')
    organization = fields.ForeignKeyField('models.Organization', related_name='discord_scheduled_events')

    # Optional event slug for categorization (e.g., tournament abbreviation)
    event_slug = fields.CharField(max_length=40, null=True)

    # Timestamps
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    class Meta:
        table = "discord_scheduled_events"
        indexes = [
            ("match_id", "organization_id"),  # Composite index for common query
        ]

    def __str__(self) -> str:
        return f"DiscordScheduledEvent(event_id={self.scheduled_event_id})"
