"""Health check endpoints."""

from fastapi import APIRouter
from api.schemas.common import HealthResponse


router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    """Simple health check endpoint."""
    return HealthResponse(status="ok", version="0.1.0")
