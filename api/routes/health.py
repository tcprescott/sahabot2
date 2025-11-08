"""Health check endpoints."""

import logging
from fastapi import APIRouter, HTTPException, Query
from api.schemas.common import HealthResponse, ServiceStatus
from config import settings
from tortoise import Tortoise
import sentry_sdk

logger = logging.getLogger(__name__)

router = APIRouter(tags=["health"])


async def check_database_health() -> ServiceStatus:
    """
    Check database connectivity.

    Returns:
        ServiceStatus: Database health status
    """
    try:
        # Try to get a connection and execute a simple query
        conn = Tortoise.get_connection("default")
        await conn.execute_query("SELECT 1")
        return ServiceStatus(status="ok", message="Database connection healthy")
    except Exception as e:
        logger.error("Database health check failed: %s", e)
        return ServiceStatus(
            status="error", message=f"Database connection failed: {str(e)}"
        )


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Health Check",
    description="Returns the health status and version of the API service. Requires a secret query parameter for authentication.",
    responses={
        200: {
            "description": "Service is healthy",
            "content": {
                "application/json": {
                    "example": {
                        "status": "ok",
                        "version": "0.1.0",
                        "services": {
                            "database": {
                                "status": "ok",
                                "message": "Database connection healthy",
                            }
                        },
                    }
                }
            },
        },
        401: {"description": "Unauthorized - Invalid or missing secret"},
    },
)
async def health(
    secret: str = Query(..., description="Health check secret for authentication")
) -> HealthResponse:
    """
    Check API service health.

    This endpoint can be used for monitoring and load balancer health checks.
    Requires a secret query parameter for authentication.

    Args:
        secret: Health check secret (configured via HEALTH_CHECK_SECRET env var)

    Returns:
        HealthResponse: Status and version information with service health details

    Raises:
        HTTPException: 401 if secret is invalid
    """
    # Validate secret
    if secret != settings.HEALTH_CHECK_SECRET:
        logger.warning("Health check attempted with invalid secret")
        raise HTTPException(status_code=401, detail="Invalid health check secret")

    # Check database health
    db_status = await check_database_health()

    # Determine overall status
    overall_status = "ok"
    if db_status.status == "error":
        overall_status = "degraded"

    return HealthResponse(
        status=overall_status, version="0.1.0", services={"database": db_status}
    )


@router.get(
    "/health/sentry-test",
    summary="Sentry Test Endpoint (Development Only)",
    description="Test endpoint to verify Sentry error tracking is working. Intentionally raises an exception. Only available in DEBUG mode.",
    responses={
        403: {"description": "Forbidden - Only available in development mode"},
        500: {"description": "Intentional test error captured by Sentry"},
    },
)
async def sentry_test():
    """
    Test Sentry error tracking.

    This endpoint intentionally raises an exception to verify that Sentry
    is properly capturing and reporting errors. This endpoint is ONLY available
    when DEBUG=True to prevent abuse in production.

    Raises:
        HTTPException: 403 if not in DEBUG mode, 500 for testing in DEBUG mode
    """
    # Only allow in DEBUG mode
    from config import settings

    if not settings.DEBUG:
        raise HTTPException(
            status_code=403,
            detail="Sentry test endpoint is only available in development mode",
        )

    # Add custom context to the error
    with sentry_sdk.push_scope() as scope:
        scope.set_tag("test_endpoint", "sentry_test")
        scope.set_context(
            "test_info",
            {
                "purpose": "Testing Sentry integration",
                "expected": "This error should appear in Sentry",
            },
        )

        # Raise an intentional error
        raise HTTPException(
            status_code=500,
            detail="This is a test error to verify Sentry integration is working",
        )
