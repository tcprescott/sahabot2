"""Common Pydantic schemas for API responses."""

from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: str
    version: str
