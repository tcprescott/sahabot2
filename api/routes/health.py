"""Health check endpoints."""

from fastapi import APIRouter, HTTPException
from api.schemas.common import HealthResponse
import sentry_sdk


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


@router.get(
    "/health/sentry-test",
    summary="Sentry Test Endpoint",
    description="Test endpoint to verify Sentry error tracking is working. Intentionally raises an exception.",
    responses={
        500: {
            "description": "Intentional test error captured by Sentry"
        }
    },
)
async def sentry_test():
    """
    Test Sentry error tracking.

    This endpoint intentionally raises an exception to verify that Sentry
    is properly capturing and reporting errors. This should only be used
    in development/testing environments.

    Raises:
        HTTPException: Always raises a 500 error for testing
    """
    # Add custom context to the error
    with sentry_sdk.push_scope() as scope:
        scope.set_tag("test_endpoint", "sentry_test")
        scope.set_context("test_info", {
            "purpose": "Testing Sentry integration",
            "expected": "This error should appear in Sentry"
        })

        # Raise an intentional error
        raise HTTPException(
            status_code=500,
            detail="This is a test error to verify Sentry integration is working"
        )
