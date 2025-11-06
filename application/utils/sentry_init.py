"""
Sentry.io initialization module.

This module provides Sentry error tracking and performance monitoring integration.
"""

import logging
import sentry_sdk
from sentry_sdk.integrations.asyncio import AsyncioIntegration
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.logging import LoggingIntegration
from config import settings

logger = logging.getLogger(__name__)


def init_sentry() -> None:
    """
    Initialize Sentry error tracking and performance monitoring.

    This function should be called during application startup, before any other
    initialization occurs. It will only initialize Sentry if SENTRY_DSN is configured.

    Features enabled:
    - Error tracking
    - Performance monitoring (traces)
    - Profiling
    - FastAPI integration
    - AsyncIO integration
    - Logging breadcrumbs
    """
    if not settings.SENTRY_DSN:
        logger.info("Sentry DSN not configured, skipping Sentry initialization")
        return

    try:
        # Determine environment name
        environment = settings.SENTRY_ENVIRONMENT or settings.ENVIRONMENT

        # Initialize Sentry with integrations
        sentry_sdk.init(
            dsn=settings.SENTRY_DSN,
            environment=environment,
            # Performance Monitoring
            traces_sample_rate=settings.SENTRY_TRACES_SAMPLE_RATE,
            # Profiling
            profiles_sample_rate=settings.SENTRY_PROFILES_SAMPLE_RATE,
            # Enable performance monitoring for FastAPI and asyncio
            integrations=[
                FastApiIntegration(transaction_style="url"),
                AsyncioIntegration(),
                LoggingIntegration(
                    level=logging.INFO,  # Capture info and above as breadcrumbs
                    event_level=logging.ERROR  # Send errors as events
                ),
            ],
            # Set release version if available
            release=f"sahabot2@0.1.0",
            # Send default PII (user info)
            send_default_pii=True,
            # Attach stack traces to all messages
            attach_stacktrace=True,
        )

        logger.info(
            "Sentry initialized successfully (environment=%s, traces_sample_rate=%s, profiles_sample_rate=%s)",
            environment,
            settings.SENTRY_TRACES_SAMPLE_RATE,
            settings.SENTRY_PROFILES_SAMPLE_RATE
        )

    except Exception as e:
        # Don't fail application startup if Sentry initialization fails
        logger.error("Failed to initialize Sentry: %s", e, exc_info=True)
