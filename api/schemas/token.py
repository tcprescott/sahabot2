"""API token schemas for API responses."""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class ApiTokenOut(BaseModel):
    """API token output schema (without token value)."""

    id: int = Field(..., description="Token ID")
    name: Optional[str] = Field(None, description="Token name/description")
    is_active: bool = Field(..., description="Whether the token is active")
    created_at: datetime = Field(..., description="Token creation timestamp")
    last_used_at: Optional[datetime] = Field(
        None, description="Last time token was used"
    )
    expires_at: Optional[datetime] = Field(
        None, description="Token expiration timestamp (null = never expires)"
    )

    class Config:
        from_attributes = True


class ApiTokenCreateResponse(BaseModel):
    """Response schema for token creation (includes plaintext token)."""

    token: str = Field(..., description="Plaintext token value (only shown once)")
    token_info: ApiTokenOut = Field(..., description="Token metadata")


class ApiTokenListResponse(BaseModel):
    """Response schema for lists of API tokens."""

    items: list[ApiTokenOut] = Field(..., description="List of token objects")
    count: int = Field(..., description="Total number of tokens in the result")


class ApiTokenCreateRequest(BaseModel):
    """Request schema for creating an API token."""

    name: Optional[str] = Field(
        None, max_length=100, description="Token name/description"
    )
    expires_at: Optional[datetime] = Field(
        None, description="Token expiration timestamp (null = never expires)"
    )
