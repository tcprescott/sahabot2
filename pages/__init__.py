"""
Pages package for SahaBot2.

This package contains all page modules.
"""

# Import pages for registration
from pages import (
    home,
    auth,
    admin,
    organization_admin,
    tournament_admin,
    async_tournament_admin,
    user_profile,
    racetime_oauth,
    twitch_oauth,
    discord_guild_callback,
    privacy,
    test
)

__all__ = [
    'home',
    'auth',
    'admin',
    'organization_admin',
    'tournament_admin',
    'async_tournament_admin',
    'user_profile',
    'racetime_oauth',
    'twitch_oauth',
    'discord_guild_callback',
    'privacy',
    'test',
]
