"""
Tortoise ORM configuration for Aerich migrations.
"""

from config import settings

TORTOISE_ORM = {
    "connections": {
        "default": settings.database_url
    },
    "apps": {
        "models": {
            "models": ["models.user", "models.audit_log", "models.api_token", "models.match_schedule", "models.organizations", "models.organization_invite", "models.settings", "models.discord_guild", "models.scheduled_task", "models.async_tournament", "aerich.models"],
            "default_connection": "default",
        }
    },
    "use_tz": True,
    "timezone": "UTC"
}
