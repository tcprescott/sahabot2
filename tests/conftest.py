"""
Pytest configuration and shared fixtures.

This file contains pytest configuration and fixtures that are available
to all tests in the test suite.
"""

import pytest
from typing import AsyncGenerator
from tortoise import Tortoise
from migrations.tortoise_config import get_model_modules


# Configure pytest-asyncio
def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", "asyncio: mark test as an async test"
    )
    config.addinivalue_line(
        "markers", "unit: mark test as a unit test"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as an integration test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )


## Use pytest-asyncio's built-in event loop (configured via asyncio_mode=auto)


@pytest.fixture(scope="function")
async def db() -> AsyncGenerator:
    """
    Initialize test database for each test function.
    
    This fixture sets up an in-memory SQLite database for testing
    and tears it down after the test completes.
    
    Yields:
        Database connection
    """
        # Initialize test database directly with explicit default connection and app mapping
    await Tortoise.init(
        config={
            "connections": {"default": "sqlite://:memory:"},
            "apps": {
                "models": {
                    "models": get_model_modules(),
                    "default_connection": "default",
                }
            },
            "use_tz": True,
            "timezone": "UTC"
        }
    )
    await Tortoise.generate_schemas()

    yield

    # Clean up
    await Tortoise.close_connections()


## Removed db_cleaner fixture: db fixture uses per-test initializer/finalizer


@pytest.fixture
def discord_user_payload():
    """
    Create a mock Discord user for testing.
    
    Returns:
        Mock Discord user data
    """
    return {
        "id": "123456789012345678",
        "username": "testuser",
        "discriminator": "0001",
        "avatar": "test_avatar_hash",
        "email": "testuser@example.com",
    }


@pytest.fixture
async def sample_user(db, discord_user_payload):
    """
    Create a sample user in the database for testing.
    
    Args:
        db: Database fixture (ensures DB is initialized)
        discord_user_payload: Discord OAuth payload fixture
        
    Returns:
        Created user instance
    """
    # Use fixtures directly instead of request.getfixturevalue
    payload = discord_user_payload

    from models.user import User, Permission

    user = await User.create(
        discord_id=int(payload["id"]),
        discord_username=payload["username"],
        discord_discriminator=payload["discriminator"],
        discord_avatar=payload["avatar"],
        discord_email=payload["email"],
        permission=Permission.USER,
        is_active=True
    )
    
    yield user
    # Cleanup handled by db fixture teardown


@pytest.fixture
async def sample_organization(db):
    """
    Create a sample organization in the database for testing.
    
    Args:
        db: Database fixture
        
    Returns:
        Created organization instance
    """
    from models.organizations import Organization

    org = await Organization.create(
        name="Test Organization",
        slug="test-org"
    )
    
    yield org
    # Cleanup handled by db fixture teardown


@pytest.fixture
async def admin_user(db, discord_user_payload):
    """
    Create an admin user in the database for testing.
    
    Args:
        db: Database fixture (ensures DB is initialized)
        discord_user_payload: Discord OAuth payload fixture
        
    Returns:
        Created admin user instance
    """
    # Use fixtures directly instead of request.getfixturevalue
    payload = discord_user_payload

    from models.user import User, Permission

    user = await User.create(
        discord_id=int(payload["id"]) + 1,
        discord_username="admin_user",
        discord_discriminator="0002",
        discord_avatar="admin_avatar_hash",
        discord_email="admin@example.com",
        permission=Permission.ADMIN,
        is_active=True
    )
    
    yield user
    # Cleanup handled by db fixture teardown


@pytest.fixture
async def sample_discord_guild(db, sample_user, sample_organization):
    """
    Create a sample Discord guild in the database for testing.
    
    Args:
        db: Database fixture
        sample_user: Sample user fixture (used as linked_by)
        sample_organization: Sample organization fixture
        
    Returns:
        Created Discord guild instance
    """
    from models.discord_guild import DiscordGuild

    guild = await DiscordGuild.create(
        organization=sample_organization,
        linked_by=sample_user,
        guild_id=987654321098765432,
        guild_name="Test Guild",
        is_active=True
    )
    
    yield guild
    # Cleanup handled by db fixture teardown


@pytest.fixture
def mock_discord_interaction(request):
    """
    Create a mock Discord interaction for testing bot commands.
    
    Args:
        mock_discord_user: Mock Discord user data
        
    Returns:
        Mock Discord interaction
    """
    from unittest.mock import MagicMock, AsyncMock
    
    # Create mock user
    payload = request.getfixturevalue('discord_user_payload')
    user = MagicMock()
    user.id = int(payload["id"])
    user.name = payload["username"]
    user.discriminator = payload["discriminator"]
    user.mention = f"<@{payload['id']}>"
    
    # Create mock interaction
    interaction = MagicMock()
    interaction.user = user
    interaction.guild_id = 987654321098765432
    interaction.channel_id = 111222333444555666
    interaction.response = AsyncMock()
    
    return interaction
