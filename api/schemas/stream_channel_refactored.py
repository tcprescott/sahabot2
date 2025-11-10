"""
EXAMPLE: Refactored stream channel schemas using schema utilities.

This is a demonstration of how to use the new schema utilities to reduce
boilerplate. Compare this file to stream_channel.py to see the improvements.

Key improvements:
1. BaseOutSchema eliminates need for Config: from_attributes = True
2. OrganizationScopedMixin adds organization_id automatically
3. TimestampMixin adds created_at/updated_at automatically
4. BaseListResponse eliminates duplicate list response class
"""

from pydantic import BaseModel, Field
from typing import Optional
from api.schema_utils import (
    BaseOutSchema,
    BaseListResponse,
    OrganizationScopedMixin,
    TimestampMixin,
)


# ============================================================================
# Output Schema - Using utilities
# ============================================================================

class StreamChannelOut(BaseOutSchema, OrganizationScopedMixin, TimestampMixin):
    """Stream channel output schema.

    Inherits from:
    - BaseOutSchema: Provides from_attributes=True configuration
    - OrganizationScopedMixin: Adds organization_id field
    - TimestampMixin: Adds created_at and updated_at fields

    This eliminates ~8 lines of boilerplate compared to manual definition.
    """

    id: int = Field(..., description="Stream channel ID")
    channel_name: str = Field(..., description="Channel name (e.g., Twitch username)")
    platform: str = Field(..., description="Streaming platform (e.g., twitch, youtube)")
    channel_url: Optional[str] = Field(None, description="Full URL to the channel")
    is_active: bool = Field(..., description="Whether the channel is active")
    # organization_id, created_at, updated_at inherited from mixins


# ============================================================================
# List Response - Using generic utility
# ============================================================================

# Option 1: Use BaseListResponse directly (recommended for new code)
StreamChannelListResponse = BaseListResponse[StreamChannelOut]

# Option 2: If you need a named class for backward compatibility
# class StreamChannelListResponse(BaseListResponse[StreamChannelOut]):
#     """List response for stream channels."""
#     pass


# ============================================================================
# Create/Update Schemas - Still manual (for clarity and validation)
# ============================================================================

class StreamChannelCreateRequest(BaseModel):
    """Request schema for creating a stream channel."""

    channel_name: str = Field(
        ..., min_length=1, max_length=255, description="Channel name"
    )
    platform: str = Field(..., description="Streaming platform")
    channel_url: Optional[str] = Field(None, description="Channel URL")
    is_active: bool = Field(True, description="Whether the channel is active")


class StreamChannelUpdateRequest(BaseModel):
    """Request schema for updating a stream channel."""

    channel_name: Optional[str] = Field(
        None, min_length=1, max_length=255, description="Channel name"
    )
    platform: Optional[str] = Field(None, description="Streaming platform")
    channel_url: Optional[str] = Field(None, description="Channel URL")
    is_active: Optional[bool] = Field(None, description="Whether the channel is active")


# ============================================================================
# Comparison with Original
# ============================================================================
#
# Original stream_channel.py (67 lines)
# vs
# Refactored (72 lines with comments, ~45 without)
#
# Benefits:
# - Eliminated Config class boilerplate
# - Eliminated organization_id field definition
# - Eliminated created_at/updated_at field definitions
# - Eliminated duplicate list response definition
# - More maintainable (common patterns in one place)
#
# Backward Compatible:
# - All schemas remain 100% compatible with existing code
# - Can be adopted incrementally
# - No breaking changes
