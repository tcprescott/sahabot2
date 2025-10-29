"""
Pytest configuration and shared fixtures.

This file contains pytest configuration and fixtures that are available
to all tests in the test suite.
"""

import pytest
import asyncio
from typing import AsyncGenerator, Generator
from tortoise import Tortoise
from tortoise.contrib.test import initializer, finalizer


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


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """
    Create an event loop for the test session.
    
    Yields:
        Event loop instance
    """
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="function")
async def db() -> AsyncGenerator:
    """
    Initialize test database for each test function.
    
    This fixture sets up an in-memory SQLite database for testing
    and tears it down after the test completes.
    
    Yields:
        Database connection
    """
    # Initialize test database
    await initializer(
        modules=["models.user", "models.audit_log"],
        db_url="sqlite://:memory:",
        app_label="models"
    )
    
    yield
    
    # Clean up
    await finalizer()


@pytest.fixture
async def clean_db(db) -> AsyncGenerator:
    """
    Provide a clean database for each test.
    
    This fixture ensures each test starts with a fresh database state.
    
    Args:
        db: Database fixture
        
    Yields:
        Database connection
    """
    # Database is already initialized by db fixture
    yield db
    
    # Clean up all tables after test
    from models.user import User
    from models.audit_log import AuditLog
    
    await User.all().delete()
    await AuditLog.all().delete()


@pytest.fixture
def mock_discord_user():
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
async def sample_user(clean_db, mock_discord_user):
    """
    Create a sample user in the database for testing.
    
    Args:
        clean_db: Clean database fixture
        mock_discord_user: Mock Discord user data
        
    Returns:
        Created user instance
    """
    from models.user import User, Permission
    
    user = await User.create(
        discord_id=int(mock_discord_user["id"]),
        discord_username=mock_discord_user["username"],
        discord_discriminator=mock_discord_user["discriminator"],
        discord_avatar=mock_discord_user["avatar"],
        discord_email=mock_discord_user["email"],
        permission=Permission.USER,
        is_active=True
    )
    
    return user


@pytest.fixture
async def admin_user(clean_db, mock_discord_user):
    """
    Create an admin user in the database for testing.
    
    Args:
        clean_db: Clean database fixture
        mock_discord_user: Mock Discord user data
        
    Returns:
        Created admin user instance
    """
    from models.user import User, Permission
    
    user = await User.create(
        discord_id=int(mock_discord_user["id"]) + 1,
        discord_username="admin_user",
        discord_discriminator="0002",
        discord_avatar="admin_avatar_hash",
        discord_email="admin@example.com",
        permission=Permission.ADMIN,
        is_active=True
    )
    
    return user


@pytest.fixture
def mock_discord_interaction(mock_discord_user):
    """
    Create a mock Discord interaction for testing bot commands.
    
    Args:
        mock_discord_user: Mock Discord user data
        
    Returns:
        Mock Discord interaction
    """
    from unittest.mock import MagicMock, AsyncMock
    
    # Create mock user
    user = MagicMock()
    user.id = int(mock_discord_user["id"])
    user.name = mock_discord_user["username"]
    user.discriminator = mock_discord_user["discriminator"]
    user.mention = f"<@{mock_discord_user['id']}>"
    
    # Create mock interaction
    interaction = MagicMock()
    interaction.user = user
    interaction.guild_id = 987654321098765432
    interaction.channel_id = 111222333444555666
    interaction.response = AsyncMock()
    
    return interaction
