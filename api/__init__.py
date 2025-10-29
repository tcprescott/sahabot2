"""
API package for SahaBot2.

This package contains FastAPI routers that expose application functionality
via HTTP endpoints. The API is part of the presentation layer and must use
the service layer exclusively (no direct ORM access).
"""

from fastapi import FastAPI
from api.routes.health import router as health_router
from api.routes.users import router as users_router


def register_api(app: FastAPI) -> None:
    """Register API routers with the FastAPI app."""
    app.include_router(health_router, prefix="/api")
    app.include_router(users_router, prefix="/api")
