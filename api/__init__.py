"""
API package for SahaBot2.

This package contains FastAPI routers that expose application functionality
via HTTP endpoints. The API is part of the presentation layer and must use
the service layer exclusively (no direct ORM access).

API routes are automatically discovered and registered from the api/routes/
directory. Any module with a 'router' attribute will be registered.
"""

from fastapi import FastAPI
from api.auto_register import auto_register_routes


def register_api(app: FastAPI) -> None:
    """
    Register API routers with the FastAPI app.

    Uses auto-discovery to find and register all route modules in api/routes/
    that have a 'router' attribute.

    Args:
        app: FastAPI application instance
    """
    auto_register_routes(app, prefix="/api")
