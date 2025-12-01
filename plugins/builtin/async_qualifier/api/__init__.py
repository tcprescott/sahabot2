"""
AsyncQualifier plugin API routes.

This module re-exports async qualifier-related API routes from the core application.
In a future phase, these routes may be moved directly into the plugin.

For now, this provides a stable import path for plugin-internal use.
"""

from api.routes.async_qualifiers import router as async_qualifiers_router
from api.routes.async_live_races import router as async_live_races_router

# Combined router for the plugin
# Note: These are separate routers in the core application
# The plugin exposes both for completeness

__all__ = [
    "async_qualifiers_router",
    "async_live_races_router",
]
