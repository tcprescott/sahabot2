"""
Services for the AOSR plugin.

This module re-exports AOSR-related services from the core application.
"""

from application.services.randomizer.aosr_service import AOSRService

__all__ = [
    "AOSRService",
]
