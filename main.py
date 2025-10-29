"""
SahaBot2 - Main Application Entry Point

This module initializes the FastAPI application with NiceGUI integration.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from nicegui import app as nicegui_app, ui
from config import settings
from database import init_db, close_db
from application.services.discord_service import DiscordService
from racetime.client import start_racetime_bot, stop_all_racetime_bots
from api import register_api
import frontend
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.

    Handles startup and shutdown events for the application.

    Args:
        app: FastAPI application instance
    """
    # Startup
    logger.info("Starting SahaBot2...")

    # Initialize database
    await init_db()
    logger.info("Database initialized")

    # Configure NiceGUI storage
    nicegui_app.storage.secret = settings.SECRET_KEY

    # Start Discord bot via service (fallback to racetime bots if unavailable)
    await DiscordService.start()

    # Start Racetime bots for configured categories
    racetime_configs = settings.racetime_bot_configs
    if racetime_configs:
        logger.info("Starting %d racetime bot(s)", len(racetime_configs))
        for category, client_id, client_secret in racetime_configs:
            try:
                await start_racetime_bot(category, client_id, client_secret)
                logger.info("Racetime bot started for category: %s", category)
            except Exception as racetime_error:
                logger.error("Failed to start Racetime bot for category %s: %s", category, racetime_error, exc_info=True)
                logger.warning("Application will continue without Racetime bot for %s", category)
    else:
        logger.info("No racetime bots configured")

    yield

    # Shutdown
    logger.info("Shutting down SahaBot2...")

    # Stop all Racetime bots
    await stop_all_racetime_bots()

    # Stop Discord bot via service
    await DiscordService.stop()

    # Close database connections
    await close_db()
    logger.info("Database connections closed")


# Initialize FastAPI application
app = FastAPI(
    title="SahaBot2 API",
    description="""
SahasrahBot2 API - A modern web application with Discord integration.

## Authentication

API endpoints use **Bearer token authentication**. Tokens are associated with Discord users
and inherit their permissions. Include your token in the `Authorization` header:

```
Authorization: Bearer YOUR_TOKEN_HERE
```

## Rate Limiting

API requests are rate limited per-user using a sliding window (default 60 requests per 60 seconds).
Per-user limits can be customized. When exceeded, the API returns HTTP 429 with a `Retry-After` header.

## Permissions

- **USER** (0) - Default permission for all authenticated users
- **MODERATOR** (50) - Can perform moderation actions
- **ADMIN** (100) - Can access admin panel and manage users
- **SUPERADMIN** (200) - Can change user permissions
    """,
    version="0.1.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_tags=[
        {
            "name": "health",
            "description": "Health check endpoints for monitoring service status.",
        },
        {
            "name": "users",
            "description": "User management endpoints. Requires authentication via Bearer token.",
        },
    ],
)

# Initialize NiceGUI with FastAPI
ui.run_with(
    app,
    storage_secret=settings.SECRET_KEY,
    title="SahaBot2",
    favicon="🤖"
)

# Register frontend routes
frontend.register_routes()

# Register API routes
register_api(app)


if __name__ in {"__main__", "__mp_main__"}:
    print(f"Starting SahaBot2 on {settings.HOST}:{settings.PORT}")
    ui.run(
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        show=False,
        storage_secret=settings.SECRET_KEY,
        title="SahaBot2",
        favicon="🤖"
    )
