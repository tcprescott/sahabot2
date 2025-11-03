"""API schemas for settings."""

from pydantic import BaseModel, Field
from typing import Optional


class SettingOut(BaseModel):
    """Schema for setting output."""

    key: str
    value: str
    description: Optional[str] = None
    is_public: Optional[bool] = None  # Only for global settings


class SettingListResponse(BaseModel):
    """Schema for setting list response."""

    items: list[SettingOut]
    count: int


class GlobalSettingCreateRequest(BaseModel):
    """Schema for creating a global setting."""

    key: str = Field(..., min_length=1, max_length=100, description="Setting key")
    value: str = Field(..., description="Setting value")
    description: Optional[str] = Field(None, max_length=500, description="Setting description")
    is_public: bool = Field(False, description="Whether setting is publicly visible")


class GlobalSettingUpdateRequest(BaseModel):
    """Schema for updating a global setting."""

    value: str = Field(..., description="Updated value")
    description: Optional[str] = Field(None, max_length=500, description="Updated description")
    is_public: Optional[bool] = Field(None, description="Updated public visibility")


class OrganizationSettingCreateRequest(BaseModel):
    """Schema for creating an organization setting."""

    key: str = Field(..., min_length=1, max_length=100, description="Setting key")
    value: str = Field(..., description="Setting value")
    description: Optional[str] = Field(None, max_length=500, description="Setting description")


class OrganizationSettingUpdateRequest(BaseModel):
    """Schema for updating an organization setting."""

    value: str = Field(..., description="Updated value")
    description: Optional[str] = Field(None, max_length=500, description="Updated description")
