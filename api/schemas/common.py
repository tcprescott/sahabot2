"""Common Pydantic schemas for API responses."""

from pydantic import BaseModel, Field
from typing import Dict, Optional


class ServiceStatus(BaseModel):
    """Status of an individual service."""

    status: str = Field(
        ...,
        description="Service status",
        examples=["ok", "error"]
    )
    message: Optional[str] = Field(
        None,
        description="Optional status message or error details"
    )


class HealthResponse(BaseModel):
    """Health check response schema."""

    status: str = Field(
        ...,
        description="Overall service health status",
        examples=["ok", "degraded", "error"]
    )
    version: str = Field(
        ...,
        description="API version number",
        examples=["0.1.0"]
    )
    services: Dict[str, ServiceStatus] = Field(
        default_factory=dict,
        description="Health status of individual upstream services"
    )
