"""API schemas for preset namespaces and randomizer presets."""

from pydantic import BaseModel, Field, field_validator
from typing import Optional
from datetime import datetime


# Preset Namespace Schemas
class PresetNamespaceOut(BaseModel):
    """Schema for preset namespace output."""

    id: int
    name: str
    description: Optional[str] = None
    owner_id: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class PresetNamespaceListResponse(BaseModel):
    """Schema for preset namespace list response."""

    items: list[PresetNamespaceOut]
    count: int


class PresetNamespaceCreateRequest(BaseModel):
    """Schema for creating a preset namespace."""

    name: str = Field(..., min_length=3, max_length=50, description="Namespace name (lowercase alphanumeric, hyphens, underscores)")
    description: Optional[str] = Field(None, max_length=500, description="Optional description")

    @field_validator('name')
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Validate namespace name format."""
        import re
        if not re.match(r'^[a-z0-9_-]+$', v):
            raise ValueError('Namespace name must contain only lowercase letters, numbers, hyphens, and underscores')
        return v


class PresetNamespaceUpdateRequest(BaseModel):
    """Schema for updating a preset namespace."""

    description: Optional[str] = Field(None, max_length=500, description="Updated description")


# Randomizer Preset Schemas
class RandomizerPresetOut(BaseModel):
    """Schema for randomizer preset output."""

    id: int
    name: str
    randomizer: str
    settings_yaml: str
    description: Optional[str] = None
    user_id: int
    namespace_id: Optional[int] = None
    namespace_name: Optional[str] = None
    is_public: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class RandomizerPresetListResponse(BaseModel):
    """Schema for randomizer preset list response."""

    items: list[RandomizerPresetOut]
    count: int


class RandomizerPresetCreateRequest(BaseModel):
    """Schema for creating a randomizer preset."""

    name: str = Field(..., min_length=1, max_length=100, description="Preset name")
    randomizer: str = Field(..., description="Randomizer type (alttpr, sm, smz3, etc.)")
    settings_yaml: str = Field(..., description="Settings in YAML format")
    description: Optional[str] = Field(None, max_length=500, description="Optional description")
    namespace_id: Optional[int] = Field(None, description="Optional namespace ID")
    is_public: bool = Field(False, description="Whether preset is publicly visible")

    @field_validator('randomizer')
    @classmethod
    def validate_randomizer(cls, v: str) -> str:
        """Validate randomizer type."""
        supported = ['alttpr', 'sm', 'smz3', 'ootr', 'aosr', 'z1r', 'ffr', 'smb3r', 'ctjets', 'bingosync']
        if v not in supported:
            raise ValueError(f'Randomizer must be one of: {", ".join(supported)}')
        return v

    @field_validator('settings_yaml')
    @classmethod
    def validate_yaml(cls, v: str) -> str:
        """Validate YAML syntax."""
        import yaml
        try:
            yaml.safe_load(v)
        except yaml.YAMLError as e:
            raise ValueError(f'Invalid YAML: {e}') from e
        return v


class RandomizerPresetUpdateRequest(BaseModel):
    """Schema for updating a randomizer preset."""

    name: Optional[str] = Field(None, min_length=1, max_length=100, description="Updated preset name")
    settings_yaml: Optional[str] = Field(None, description="Updated settings in YAML format")
    description: Optional[str] = Field(None, max_length=500, description="Updated description")
    is_public: Optional[bool] = Field(None, description="Updated public visibility")

    @field_validator('settings_yaml')
    @classmethod
    def validate_yaml(cls, v: Optional[str]) -> Optional[str]:
        """Validate YAML syntax if provided."""
        if v is not None:
            import yaml
            try:
                yaml.safe_load(v)
            except yaml.YAMLError as e:
                raise ValueError(f'Invalid YAML: {e}') from e
        return v
