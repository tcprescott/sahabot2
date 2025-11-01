"""Organization schemas for API responses."""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class OrganizationOut(BaseModel):
    """Organization output schema."""

    id: int = Field(..., description="Organization ID")
    name: str = Field(..., description="Organization name")
    description: Optional[str] = Field(None, description="Organization description")
    is_active: bool = Field(..., description="Whether the organization is active")
    created_at: datetime = Field(..., description="Organization creation timestamp")
    updated_at: datetime = Field(..., description="Organization last update timestamp")

    class Config:
        from_attributes = True


class OrganizationListResponse(BaseModel):
    """Response schema for lists of organizations."""

    items: list[OrganizationOut] = Field(..., description="List of organization objects")
    count: int = Field(..., description="Total number of organizations in the result")


class OrganizationCreateRequest(BaseModel):
    """Request schema for creating an organization."""

    name: str = Field(..., min_length=1, max_length=255, description="Organization name")
    description: Optional[str] = Field(None, description="Organization description")
    is_active: bool = Field(True, description="Whether the organization should be active")


class OrganizationUpdateRequest(BaseModel):
    """Request schema for updating an organization."""

    name: Optional[str] = Field(None, min_length=1, max_length=255, description="Organization name")
    description: Optional[str] = Field(None, description="Organization description")
    is_active: Optional[bool] = Field(None, description="Whether the organization is active")


class OrganizationPermissionOut(BaseModel):
    """Organization permission output schema."""

    id: int = Field(..., description="Permission ID")
    organization_id: int = Field(..., description="Organization ID")
    permission_name: str = Field(..., description="Permission name")
    description: Optional[str] = Field(None, description="Permission description")
    created_at: datetime = Field(..., description="Permission creation timestamp")
    updated_at: datetime = Field(..., description="Permission last update timestamp")

    class Config:
        from_attributes = True


class OrganizationPermissionListResponse(BaseModel):
    """Response schema for lists of organization permissions."""

    items: list[OrganizationPermissionOut] = Field(..., description="List of permission objects")
    count: int = Field(..., description="Total number of permissions in the result")


class OrganizationPermissionCreateRequest(BaseModel):
    """Request schema for creating an organization permission."""

    permission_name: str = Field(..., min_length=1, max_length=100, description="Permission name")
    description: Optional[str] = Field(None, description="Permission description")


class OrganizationMemberOut(BaseModel):
    """Organization member output schema."""

    id: int = Field(..., description="Member ID")
    organization_id: int = Field(..., description="Organization ID")
    user_id: int = Field(..., description="User ID")
    permissions: list[str] = Field(default_factory=list, description="List of permission names assigned to this member")
    joined_at: datetime = Field(..., description="Member join timestamp")
    updated_at: datetime = Field(..., description="Member last update timestamp")

    class Config:
        from_attributes = True


class OrganizationMemberListResponse(BaseModel):
    """Response schema for lists of organization members."""

    items: list[OrganizationMemberOut] = Field(..., description="List of member objects")
    count: int = Field(..., description="Total number of members in the result")


class OrganizationMemberPermissionsUpdateRequest(BaseModel):
    """Request schema for updating member permissions."""

    permission_names: list[str] = Field(..., description="List of permission names to assign to the member")
