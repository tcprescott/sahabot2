"""
RaceTime Room model.

Stores active RaceTime race room state, decoupled from Match model.
This allows better tracking of room lifecycle and prevents orphaned room slugs.
"""
from __future__ import annotations
from tortoise import fields
from tortoise.models import Model


class RacetimeRoom(Model):
    """
    Active RaceTime race room.

    Tracks state of open race rooms. When a room is created or joined,
    a RacetimeRoom record is created. When the race is finished or cancelled,
    the record is deleted.

    This decouples room tracking from Match, allowing:
    - Better room lifecycle management
    - Prevention of orphaned room slugs
    - Easier querying of active rooms
    - Room-specific metadata storage
    """
    id = fields.IntField(pk=True)
    
    # Room identification
    slug = fields.CharField(max_length=255, unique=True, description="Full room slug (e.g., 'alttpr/cool-doge-1234')")
    category = fields.CharField(max_length=50, description="RaceTime category (e.g., 'alttpr')")
    room_name = fields.CharField(max_length=255, description="Room name only (e.g., 'cool-doge-1234')")
    
    # Room state
    status = fields.CharField(max_length=50, null=True, description="Current race status (open, pending, in_progress, finished, cancelled)")
    
    # Relationships
    match = fields.OneToOneField(
        'models.Match',
        related_name='racetime_room',
        null=True,
        on_delete=fields.SET_NULL,
        description="Associated tournament match (if any)"
    )
    bot = fields.ForeignKeyField(
        'models.RacetimeBot',
        related_name='active_rooms',
        null=True,
        on_delete=fields.SET_NULL,
        description="Bot managing this room"
    )
    
    # Metadata
    created_at = fields.DatetimeField(auto_now_add=True, description="When room was created or joined")
    updated_at = fields.DatetimeField(auto_now=True, description="Last status update")
    
    class Meta:
        table = "racetime_rooms"
    
    def __str__(self) -> str:
        return f"{self.slug} ({self.status or 'unknown'})"
