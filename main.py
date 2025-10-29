"""
SahaBot2 - Main Application Entry Point

This module initializes the FastAPI application with NiceGUI integration.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from nicegui import app as nicegui_app, ui
from config import settings
from database import init_db, close_db
import frontend


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.
    
    Handles startup and shutdown events for the application.
    
    Args:
        app: FastAPI application instance
    """
    # Startup
    print("Starting SahaBot2...")
    await init_db()
    print("Database initialized")
    
    # Configure NiceGUI storage
    nicegui_app.storage.secret = settings.SECRET_KEY
    
    yield
    
    # Shutdown
    print("Shutting down SahaBot2...")
    await close_db()
    print("Database connections closed")


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
