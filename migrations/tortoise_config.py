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
            "models": ["models.user", "models.audit_log", "models.api_token", "models.match_schedule", "models.organizations", "models.organization_invite", "models.organization_request", "models.settings", "models.discord_guild", "models.scheduled_task", "models.async_tournament", "models.tournament_usage", "models.randomizer_preset", "models.preset_namespace", "models.preset_namespace_permission", "models.racetime_bot", "models.notification_subscription", "models.notification_log", "aerich.models"],
            "default_connection": "default",
        }
    },
    "use_tz": True,
    "timezone": "UTC"
}
