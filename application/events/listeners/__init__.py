"""
Event listeners organized by domain.

This module imports all domain-specific listeners to ensure they are registered
when the events module is imported.
"""

import logging

# Import all listener modules to register their handlers
from application.events.listeners import (
    user_listeners,
    organization_listeners,
    tournament_listeners,
    race_listeners,
    match_listeners,
    notification_listeners,
    discord_listeners,
    racetime_listeners,
)

logger = logging.getLogger(__name__)

__all__ = [
    "user_listeners",
    "organization_listeners",
    "tournament_listeners",
    "race_listeners",
    "match_listeners",
    "notification_listeners",
    "discord_listeners",
    "racetime_listeners",
]

# All event listeners are now registered via the domain-specific modules
logger.info("Event listeners registered")
