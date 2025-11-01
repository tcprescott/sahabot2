"""
Auto-registration utility for API routes.

This module provides automatic discovery and registration of API route modules.
Any Python file in api/routes/ that has a 'router' attribute will be automatically
discovered and registered with the FastAPI application.
"""

import logging
from pathlib import Path
from importlib import import_module
from fastapi import FastAPI

logger = logging.getLogger(__name__)


def auto_register_routes(app: FastAPI, prefix: str = "/api") -> None:
    """
    Automatically discover and register all route modules.

    Scans the api/routes/ directory for Python files and registers any
    that have a 'router' attribute (FastAPI APIRouter instance).

    Files starting with underscore (_) are skipped.

    Args:
        app: FastAPI application instance
        prefix: URL prefix for all routes (default: "/api")

    Example:
        >>> app = FastAPI()
        >>> auto_register_routes(app)
        # Registers all routes from api/routes/*.py
    """
    routes_dir = Path(__file__).parent / "routes"

    if not routes_dir.exists():
        logger.warning("Routes directory not found: %s", routes_dir)
        return

    registered_count = 0
    failed_count = 0

    for route_file in sorted(routes_dir.glob("*.py")):
        # Skip private files and __init__.py
        if route_file.stem.startswith("_"):
            continue

        module_name = f"api.routes.{route_file.stem}"

        try:
            module = import_module(module_name)

            if hasattr(module, "router"):
                app.include_router(module.router, prefix=prefix)
                logger.info("Registered API routes from %s", module_name)
                registered_count += 1
            else:
                logger.debug(
                    "Skipping %s - no 'router' attribute found",
                    module_name
                )

        except Exception as e:
            logger.error(
                "Failed to load %s: %s",
                module_name,
                str(e),
                exc_info=True
            )
            failed_count += 1

    logger.info(
        "API route registration complete: %s registered, %s failed",
        registered_count,
        failed_count
    )


def register_route_module(
    app: FastAPI,
    module_name: str,
    prefix: str = "/api"
) -> bool:
    """
    Manually register a specific route module.

    This is useful when you want to register routes manually rather than
    using auto-discovery, or when testing specific route modules.

    Args:
        app: FastAPI application instance
        module_name: Full module name (e.g., "api.routes.users")
        prefix: URL prefix for routes (default: "/api")

    Returns:
        bool: True if registration succeeded, False otherwise

    Example:
        >>> app = FastAPI()
        >>> register_route_module(app, "api.routes.users")
        True
    """
    try:
        module = import_module(module_name)

        if not hasattr(module, "router"):
            logger.error(
                "Module %s does not have a 'router' attribute",
                module_name
            )
            return False

        app.include_router(module.router, prefix=prefix)
        logger.info("Registered API routes from %s", module_name)
        return True

    except Exception as e:
        logger.error(
            "Failed to load %s: %s",
            module_name,
            str(e),
            exc_info=True
        )
        return False
