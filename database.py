"""
Database initialization and management utilities.
"""

from tortoise import Tortoise
from config import settings


async def init_db() -> None:
    """
    Initialize database connection.
    
    This should be called during application startup.
    """
    await Tortoise.init(
        db_url=settings.database_url,
        modules={'models': ['models.user', 'models.audit_log', 'models.api_token']},
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
