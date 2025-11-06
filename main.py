"""
SahaBot2 - Main Application Entry Point

This module initializes the FastAPI application with NiceGUI integration.
"""

import logging
import asyncio

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from nicegui import app as nicegui_app, ui
from config import settings
from database import init_db, close_db
from application.services.discord.discord_service import DiscordService
from application.services.racetime.racetime_service import RacetimeService
from application.services.tasks.task_scheduler_service import TaskSchedulerService
from application.services.tasks.task_handlers import register_task_handlers
from application.services.notifications.notification_processor import start_notification_processor, stop_notification_processor
from middleware.security import SecurityHeadersMiddleware, HTTPSRedirectMiddleware
from api import register_api
import frontend

# Import to register event listeners
import application.events.listeners  # noqa: F401

# Initialize Sentry (must be done early, before other imports)
from application.utils.sentry_init import init_sentry
init_sentry()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize in-memory log handler for admin UI
from application.utils.log_handler import init_log_handler
init_log_handler(max_records=1000)


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

    # Event system is automatically initialized via import
    logger.info("Event system initialized with registered listeners")

    # Configure NiceGUI storage
    nicegui_app.storage.secret = settings.SECRET_KEY

    # Start Discord bot via service (if enabled)
    if settings.DISCORD_BOT_ENABLED:
        await DiscordService.start()
    else:
        logger.info("Discord bot disabled by configuration")

    # Start Racetime bots in background (non-blocking) - they'll start after app is running
    async def start_racetime_bots_background():
        """Start racetime bots in background without blocking startup."""
        try:
            logger.info("Starting racetime bots in background...")
            started = await RacetimeService.start_all()
            logger.info("Started %d racetime bot(s) in background", started)
        except Exception as e:
            logger.error("Error starting racetime bots: %s", e, exc_info=True)

    # Schedule the background task (don't await it)
    asyncio.create_task(start_racetime_bots_background())
    logger.info("Racetime bots scheduled to start in background")

    # Register task handlers
    register_task_handlers()

    # Start task scheduler
    await TaskSchedulerService.start_scheduler()
    logger.info("Task scheduler started")

    # Start notification processor
    await start_notification_processor()
    logger.info("Notification processor started")

    yield

    # Shutdown
    logger.info("Shutting down SahaBot2...")

    # Stop notification processor
    await stop_notification_processor()
    logger.info("Notification processor stopped")

    # Stop task scheduler
    await TaskSchedulerService.stop_scheduler()
    logger.info("Task scheduler stopped")

    # Stop all Racetime bots
    await RacetimeService.stop_all()

    # Stop Discord bot via service (if it was enabled)
    if settings.DISCORD_BOT_ENABLED:
        await DiscordService.stop()

    # Close database connections
    await close_db()
    logger.info("Database connections closed")


# Initialize FastAPI application
app: FastAPI = FastAPI(
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

# Configure CORS
# In production, this is restricted to BASE_URL only
# In development, allows all origins for convenience during local development
# NOTE: The wildcard '*' in development mode can expose the application to
# cross-origin attacks. For a more secure development setup, replace with:
# allowed_origins = [settings.BASE_URL, "http://localhost:8080", "http://localhost:3000"]
allowed_origins = ["*"] if settings.DEBUG else [settings.BASE_URL]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
    allow_headers=["*"],
    max_age=3600,  # Cache preflight requests for 1 hour
)

# Add security middleware
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(HTTPSRedirectMiddleware)

# Register API routes
register_api(app)

# Register frontend routes (including static files mounting)
frontend.register_routes(app)

# Initialize NiceGUI with FastAPI
ui.run_with(
    app,
    storage_secret=settings.SECRET_KEY,
    title="SahaBot2",
    favicon="🤖"
)


if __name__ in {"__main__", "__mp_main__"}:
    logger.info("Starting SahaBot2 on %s:%s", settings.HOST, settings.PORT)
    ui.run(
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        show=False,
        storage_secret=settings.SECRET_KEY,
        title="SahaBot2",
        favicon="🤖"
    )
