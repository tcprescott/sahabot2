"""Common Pydantic schemas for API responses."""

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    """Health check response schema."""
    
    status: str = Field(
        ...,
        description="Service health status",
        examples=["ok", "degraded", "error"]
    )
    version: str = Field(
        ...,
        description="API version number",
        examples=["0.1.0"]
    )
