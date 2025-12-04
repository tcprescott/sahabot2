"""Pages package for SahaBot2.

Exports NiceGUI page modules for registration.
"""

from . import (
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

__all__ = [
    "home",
    "auth",
    "admin",
    "organization_admin",
    "async_qualifier_admin",
    "async_qualifiers",
    "user_profile",
    "invite",
    "racetime_oauth",
    "twitch_oauth",
    "discord_guild_callback",
    "privacy",
    "test",
]
