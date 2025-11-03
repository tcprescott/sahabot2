"""
Database initialization and management utilities.
"""

from tortoise import Tortoise
from config import settings
from migrations.tortoise_config import TORTOISE_ORM
from aerich import Command

async def init_db() -> None:
    """
    Initialize database connection.

    This should be called during application startup.
    """
    command = Command(tortoise_config=TORTOISE_ORM, app='models', location='./migrations')
    await command.init()
    await command.upgrade()
    await Tortoise.init(
        db_url=settings.database_url,
        modules={'models': ['models.user', 'models.audit_log', 'models.api_token', 'models.match_schedule', 'models.organizations', 'models.organization_invite', 'models.settings', 'models.async_tournament', 'models.scheduled_task']},
        use_tz=True,
        timezone='UTC'
    )


async def close_db() -> None:
    """
    Close database connections.

    This should be called during application shutdown.
    """
    await Tortoise.close_connections()


async def generate_schemas() -> None:
    """
    Generate database schemas.

    Only use this in development. In production, use Aerich migrations.
    """
    await Tortoise.generate_schemas()
