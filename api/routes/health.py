"""Health check endpoints."""

from fastapi import APIRouter
from api.schemas.common import HealthResponse


router = APIRouter(tags=["health"])


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Health Check",
    description="Returns the health status and version of the API service.",
    responses={
        200: {
            "description": "Service is healthy",
            "content": {
                "application/json": {
                    "example": {"status": "ok", "version": "0.1.0"}
                }
            },
        }
    },
)
async def health() -> HealthResponse:
    """
    Check API service health.
    
    This endpoint can be used for monitoring and load balancer health checks.
    No authentication required.
    
    Returns:
        HealthResponse: Status and version information
    """
    return HealthResponse(status="ok", version="0.1.0")
