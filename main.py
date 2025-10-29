"""
SahaBot2 - Main Application Entry Point

This module initializes the FastAPI application with NiceGUI integration.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from nicegui import app as nicegui_app, ui
from config import settings
from database import init_db, close_db
from bot.client import start_bot, stop_bot
from racetime.client import start_racetime_bot, stop_all_racetime_bots
import frontend
import api
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    """
    Application lifespan manager.
    
    Handles startup and shutdown events for the application.
    
    Args:
        _app: FastAPI application instance (unused)
    """
    # Startup
    logger.info("Starting SahaBot2...")
    
    # Initialize database
    await init_db()
    logger.info("Database initialized")
    
    # Configure NiceGUI storage
    nicegui_app.storage.secret = settings.SECRET_KEY
    
    # Start Discord bot
    try:
        await start_bot()
        logger.info("Discord bot started")
    except Exception as e:
        logger.error("Failed to start Discord bot: %s", e, exc_info=True)
        logger.warning("Application will continue without Discord bot")

    # Start Racetime bots for configured categories
    racetime_configs = settings.racetime_bot_configs
    if racetime_configs:
        logger.info("Starting %d racetime bot(s)", len(racetime_configs))
        for category, client_id, client_secret in racetime_configs:
            try:
                await start_racetime_bot(category, client_id, client_secret)
                logger.info("Racetime bot started for category: %s", category)
            except Exception as e:
                logger.error("Failed to start Racetime bot for category %s: %s", category, e, exc_info=True)
                logger.warning("Application will continue without Racetime bot for %s", category)
    else:
        logger.info("No racetime bots configured")
    
    yield
    
    # Shutdown
    logger.info("Shutting down SahaBot2...")
    
    # Stop all Racetime bots
    await stop_all_racetime_bots()
    
    # Stop Discord bot
    try:
        await stop_bot()
        logger.info("Discord bot stopped")
    except Exception as e:
        logger.error("Error stopping Discord bot: %s", e, exc_info=True)
    
    # Close database connections
    await close_db()
    logger.info("Database connections closed")


# Initialize FastAPI application
app = FastAPI(
    title="SahaBot2",
    description="SahasrahBot2 - A NiceGUI + Tortoise ORM web application",
    version="0.1.0",
    lifespan=lifespan
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

# Register API routers
api.register_api(app)


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
