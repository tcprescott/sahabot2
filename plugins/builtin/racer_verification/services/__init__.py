"""
RacerVerification Plugin services.

This module re-exports racer verification services from the core application
to provide a unified interface through the plugin system.
"""

from application.services.racetime.racer_verification_service import (
    RacerVerificationService,
)

__all__ = [
    "RacerVerificationService",
]
