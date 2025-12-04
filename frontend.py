"""
Frontend routes registration.

This module registers all NiceGUI pages and routes for the application.
"""

import logging
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from config import settings
from pages import (
    home,
    auth,
    admin,
    organization_admin,
    async_qualifier_admin,
    async_qualifiers,
    user_profile,
    invite,
    racetime_oauth,
    twitch_oauth,
    discord_guild_callback,
    privacy,
    test,
)
from modules.tournament.pages import (
    tournament_admin,
    tournament_match_settings,
    tournaments,
)

logger = logging.getLogger(__name__)


class NoCacheStaticFiles(StaticFiles):
    """StaticFiles subclass that disables caching in development mode."""

    def __init__(self, *args, **kwargs):
        self.is_dev = settings.DEBUG
        super().__init__(*args, **kwargs)

    async def __call__(self, scope, receive, send):
        if self.is_dev and scope["type"] == "http":
            # Wrap the send function to add no-cache headers
            async def send_wrapper(message):
                if message["type"] == "http.response.start":
                    headers = list(message.get("headers", []))
                    # Remove any existing cache-control headers
                    headers = [h for h in headers if h[0].lower() != b"cache-control"]
                    # Add no-cache headers
                    headers.append(
                        (b"cache-control", b"no-cache, no-store, must-revalidate")
                    )
                    headers.append((b"pragma", b"no-cache"))
                    headers.append((b"expires", b"0"))
                    message["headers"] = headers
                await send(message)

            await super().__call__(scope, receive, send_wrapper)
        else:
            await super().__call__(scope, receive, send)


def register_routes(fastapi_app: FastAPI = None):
    """
    Register all frontend routes and mount static files.

    This function is called from main.py to register all NiceGUI pages.

    Args:
        fastapi_app: The FastAPI application instance (optional, for mounting static files)
    """
    # Mount static files directory with no-cache in development
    if fastapi_app:
        fastapi_app.mount(
            "/static", NoCacheStaticFiles(directory="static"), name="static"
        )

    # Register pages
    # Register more specific routes before catch-all routes
    auth.register()
    user_profile.register()
    admin.register()
    organization_admin.register()
    tournament_admin.register()
    async_qualifier_admin.register()
    tournaments.register()
    async_qualifiers.register()
    tournament_match_settings.register()
    # Home page with /{view} catch-all must be last
    home.register()
    invite.register()
    racetime_oauth.register()
    twitch_oauth.register()
    discord_guild_callback.register()
    privacy.register()
    test.register()  # Only registers if DEBUG is enabled

    logger.info("Frontend routes registered")
