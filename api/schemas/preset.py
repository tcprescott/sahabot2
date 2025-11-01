"""
Preset API schemas.

Pydantic models for preset API requests and responses.
"""

from typing import Optional, List, Dict
from pydantic import BaseModel, Field
from datetime import datetime


class PresetNamespaceBase(BaseModel):
    """Base schema for preset namespace."""
    name: str = Field(..., min_length=1, max_length=255)
    is_public: bool = True
    description: Optional[str] = None


class PresetNamespaceCreate(PresetNamespaceBase):
    """Schema for creating a preset namespace."""
    pass


class PresetNamespaceResponse(PresetNamespaceBase):
    """Schema for preset namespace response."""
    id: int
    owner_discord_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        """Pydantic configuration."""
        from_attributes = True


class PresetBase(BaseModel):
    """Base schema for preset."""
    preset_name: str = Field(..., min_length=1, max_length=255)
    randomizer: str = Field(..., min_length=1, max_length=50)
    content: str = Field(..., min_length=1)
    description: Optional[str] = None


class PresetCreate(PresetBase):
    """Schema for creating a preset."""
    namespace_name: str = Field(..., min_length=1, max_length=255)


class PresetUpdate(BaseModel):
    """Schema for updating a preset."""
    content: Optional[str] = Field(None, min_length=1)
    description: Optional[str] = None


class PresetResponse(PresetBase):
    """Schema for preset response."""
    id: int
    namespace: PresetNamespaceResponse
    created_at: datetime
    updated_at: datetime

    class Config:
        """Pydantic configuration."""
        from_attributes = True


class PresetListItem(BaseModel):
    """Schema for preset list item (minimal info)."""
    id: int
    preset_name: str
    randomizer: str
    namespace_name: str
    description: Optional[str] = None

    class Config:
        """Pydantic configuration."""
        from_attributes = True


class PresetListResponse(BaseModel):
    """Schema for preset list response."""
    items: List[PresetListItem]
    count: int


class NamespaceListResponse(BaseModel):
    """Schema for namespace list response."""
    items: List[PresetNamespaceResponse]
    count: int


class PresetsByRandomizerResponse(BaseModel):
    """Schema for presets grouped by randomizer."""
    randomizer: str
    presets: Dict[str, List[str]]  # namespace_name -> [preset_names]


class PresetContentResponse(BaseModel):
    """Schema for preset content as parsed YAML."""
    preset_name: str
    randomizer: str
    namespace_name: str
    settings: Dict  # Parsed YAML content
