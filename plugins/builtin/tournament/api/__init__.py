"""
Tournament plugin API routes.

This module re-exports tournament-related API routes from the core application.
In a future phase, these routes may be moved directly into the plugin.

For now, this provides a stable import path for plugin-internal use.
"""

from api.routes.tournaments import router

__all__ = ["router"]
