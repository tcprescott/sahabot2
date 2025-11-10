"""
Sentry.io initialization module.

This module provides Sentry error tracking and performance monitoring integration.
"""

import logging
import os
import sentry_sdk
from sentry_sdk.integrations.asyncio import AsyncioIntegration
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.logging import LoggingIntegration
from config import settings

logger = logging.getLogger(__name__)


def _get_release_version() -> str:
    """
    Get the release version for Sentry.

    Checks for version in the following order:
    1. SENTRY_RELEASE from settings
    2. Git commit SHA (if .git directory exists)
    3. Default version from pyproject.toml

    Returns:
        str: Release version string
    """
    # Check for explicit SENTRY_RELEASE in settings
    if settings.SENTRY_RELEASE:
        return settings.SENTRY_RELEASE

    # Try to get git commit SHA
    try:
        import subprocess

        result = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            capture_output=True,
            text=True,
            timeout=1,
            cwd=os.path.dirname(os.path.abspath(__file__)),
        )
        if result.returncode == 0:
            commit_sha = result.stdout.strip()
            if commit_sha:
                return f"sahabot2@{commit_sha}"
    except (subprocess.TimeoutExpired, FileNotFoundError, Exception) as e:
        # Failed to get git commit SHA; falling back to default version.
        logger.debug(
            "Could not determine git commit SHA for Sentry release version: %s",
            e,
            exc_info=True,
        )

    # Fallback to default version
    return "sahabot2@0.1.0"


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
                    event_level=logging.ERROR,  # Send errors as events
                ),
            ],
            # Set release version (git commit or default)
            release=_get_release_version(),
            # Send default PII (user info)
            send_default_pii=True,
            # Attach stack traces to all messages
            attach_stacktrace=True,
        )

        logger.info(
            "Sentry initialized successfully (environment=%s, traces_sample_rate=%s, profiles_sample_rate=%s)",
            environment,
            settings.SENTRY_TRACES_SAMPLE_RATE,
            settings.SENTRY_PROFILES_SAMPLE_RATE,
        )

    except Exception as e:
        # Don't fail application startup if Sentry initialization fails
        logger.error("Failed to initialize Sentry: %s", e, exc_info=True)
