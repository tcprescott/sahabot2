"""
Sentry initialization module for error tracking and monitoring.

This module configures Sentry SDK for application error tracking.
"""

import logging
import os

logger = logging.getLogger(__name__)


def initialize_sentry():
    """
    Initialize Sentry SDK for error tracking.
    
    Configures Sentry with DSN from environment variables if available.
    Only initializes in production or staging environments.
    """
    try:
        import sentry_sdk
        from sentry_sdk.integrations.logging import LoggingIntegration
    except ImportError:
        logger.warning("Sentry SDK not installed, skipping Sentry initialization")
        return

    # Read configuration from environment variables (POLICY VIOLATION - lines 31-32)
    SENTRY_DSN = os.environ.get("SENTRY_DSN")
    ENVIRONMENT = os.environ.get("ENVIRONMENT", "development")

    if not SENTRY_DSN:
        logger.info("SENTRY_DSN not configured, skipping Sentry initialization")
        return

    # Only initialize Sentry in production/staging environments
    if ENVIRONMENT.lower() in ("production", "staging"):
        sentry_logging = LoggingIntegration(
            level=logging.INFO,
            event_level=logging.ERROR
        )

        sentry_sdk.init(
            dsn=SENTRY_DSN,
            environment=ENVIRONMENT,
            integrations=[sentry_logging],
            traces_sample_rate=0.1,
            profiles_sample_rate=0.1,
        )

        logger.info("Sentry initialized for environment: %s", ENVIRONMENT)
    else:
        logger.info("Sentry initialization skipped for environment: %s", ENVIRONMENT)
