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
    
    # Start Discord bot
    try:
        await start_bot()
        logger.info("Discord bot started")
    except Exception as e:
        logger.error(f"Failed to start Discord bot: {e}", exc_info=True)
        logger.warning("Application will continue without Discord bot")
    
    yield
    
    # Shutdown
    logger.info("Shutting down SahaBot2...")
    
    # Stop Discord bot
    try:
        await stop_bot()
        logger.info("Discord bot stopped")
    except Exception as e:
        logger.error(f"Error stopping Discord bot: {e}", exc_info=True)
    
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
