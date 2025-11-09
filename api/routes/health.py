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


async def check_discord_health() -> ServiceStatus:
    """
    Check Discord bot connectivity.

    Returns:
        ServiceStatus: Discord bot health status
    """
    try:
        from discordbot.client import get_bot_instance

        bot = get_bot_instance()
        if bot is None:
            return ServiceStatus(
                status="error", message="Discord bot not started or disabled"
            )

        if bot.is_ready():
            return ServiceStatus(status="ok", message="Discord bot connected and ready")
        else:
            return ServiceStatus(
                status="error", message="Discord bot not ready or disconnected"
            )
    except Exception as e:
        logger.error("Discord health check failed: %s", e)
        return ServiceStatus(
            status="error", message=f"Discord health check failed: {str(e)}"
        )


async def check_racetime_health() -> ServiceStatus:
    """
    Check RaceTime bot connectivity.

    Returns:
        ServiceStatus: RaceTime bot health status
    """
    try:
        from racetime.client import get_all_racetime_bot_instances

        bots = get_all_racetime_bot_instances()
        if not bots:
            return ServiceStatus(
                status="error", message="No RaceTime bots running or configured"
            )

        # Count active bots
        bot_count = len(bots)
        categories = ", ".join(bots.keys())

        return ServiceStatus(
            status="ok",
            message=f"{bot_count} RaceTime bot(s) running for categories: {categories}",
        )
    except Exception as e:
        logger.error("RaceTime health check failed: %s", e)
        return ServiceStatus(
            status="error", message=f"RaceTime health check failed: {str(e)}"
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
                            },
                            "discord": {
                                "status": "ok",
                                "message": "Discord bot connected and ready",
                            },
                            "racetime": {
                                "status": "ok",
                                "message": "2 RaceTime bot(s) running for categories: alttpr, smz3",
                            },
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

    # Check all services
    db_status = await check_database_health()
    discord_status = await check_discord_health()
    racetime_status = await check_racetime_health()

    # Determine overall status
    overall_status = "ok"
    services = {
        "database": db_status,
        "discord": discord_status,
        "racetime": racetime_status,
    }

    # If any service has an error, overall status is degraded
    for service_status in services.values():
        if service_status.status == "error":
            overall_status = "degraded"
            break

    return HealthResponse(status=overall_status, version="0.1.0", services=services)


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
