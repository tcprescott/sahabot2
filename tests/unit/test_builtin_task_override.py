"""
Unit tests for builtin task override functionality.

Tests the business logic for disabling built-in tasks via database.
"""

import pytest
from models.user import User, Permission
from application.repositories.builtin_task_override_repository import BuiltinTaskOverrideRepository
from application.services.tasks.task_scheduler_service import TaskSchedulerService


@pytest.fixture
async def regular_user(db):
    """Create a regular user for testing."""
    user = await User.create(
        discord_id=999888777,
        discord_username="regular_user",
        discord_discriminator="0003",
        discord_avatar="regular_avatar",
        discord_email="regular@example.com",
        permission=Permission.USER,
        is_active=True
    )
    yield user


@pytest.mark.unit
class TestBuiltinTaskOverride:
    """Test cases for builtin task override functionality."""

    @pytest.mark.asyncio
    async def test_create_override(self, db):
        """Test creating a builtin task override."""
        repo = BuiltinTaskOverrideRepository()

        override = await repo.create(
            task_id='test_task',
            is_active=False
        )

        assert override is not None
        assert override.task_id == 'test_task'
        assert override.is_active is False

    @pytest.mark.asyncio
    async def test_get_by_task_id(self, db):
        """Test retrieving a builtin task override by task ID."""
        repo = BuiltinTaskOverrideRepository()

        # Create override
        await repo.create(task_id='test_task_2', is_active=True)

        # Retrieve it
        override = await repo.get_by_task_id('test_task_2')

        assert override is not None
        assert override.task_id == 'test_task_2'
        assert override.is_active is True

    @pytest.mark.asyncio
    async def test_set_active_creates_if_not_exists(self, db):
        """Test that set_active creates an override if it doesn't exist."""
        repo = BuiltinTaskOverrideRepository()

        override = await repo.set_active('new_task', False)

        assert override is not None
        assert override.task_id == 'new_task'
        assert override.is_active is False

    @pytest.mark.asyncio
    async def test_set_active_updates_if_exists(self, db):
        """Test that set_active updates an existing override."""
        repo = BuiltinTaskOverrideRepository()

        # Create initial override
        await repo.create(task_id='update_task', is_active=True)

        # Update it
        override = await repo.set_active('update_task', False)

        assert override is not None
        assert override.task_id == 'update_task'
        assert override.is_active is False

    @pytest.mark.asyncio
    async def test_get_overrides_dict(self, db):
        """Test getting all overrides as a dictionary."""
        repo = BuiltinTaskOverrideRepository()

        # Create multiple overrides
        await repo.create(task_id='task_1', is_active=True)
        await repo.create(task_id='task_2', is_active=False)
        await repo.create(task_id='task_3', is_active=True)

        # Get as dict
        overrides_dict = await repo.get_overrides_dict()

        assert len(overrides_dict) >= 3
        assert overrides_dict['task_1'] is True
        assert overrides_dict['task_2'] is False
        assert overrides_dict['task_3'] is True

    @pytest.mark.asyncio
    async def test_effective_active_status_with_override(self, db, admin_user):
        """Test that effective active status respects database override."""
        service = TaskSchedulerService()
        
        # Create an override in the database (using an actual builtin task)
        await service.set_builtin_task_active(admin_user, 'cleanup_tournament_usage', False)
        
        # Check effective status
        effective = TaskSchedulerService.get_effective_active_status('cleanup_tournament_usage', True)

        # Should use override (False) instead of default (True)
        assert effective is False

    @pytest.mark.asyncio
    async def test_effective_active_status_without_override(self):
        """Test that effective active status falls back to default without override."""
        # Clear cache to simulate no override
        TaskSchedulerService.clear_builtin_task_overrides_cache()

        # Check effective status (using a real builtin task)
        effective = TaskSchedulerService.get_effective_active_status('cleanup_tournament_usage', True)

        # Should use default (True) since no override exists
        assert effective is True

    @pytest.mark.asyncio
    async def test_set_builtin_task_active_unauthorized(self, db, regular_user):
        """Test that non-admin users cannot toggle builtin task status."""
        service = TaskSchedulerService()

        # Try to set with regular user (should fail)
        success = await service.set_builtin_task_active(
            regular_user,
            'cleanup_tournament_usage',
            False
        )

        assert success is False

    @pytest.mark.asyncio
    async def test_set_builtin_task_active_authorized(self, db, admin_user):
        """Test that admin users can toggle builtin task status."""
        service = TaskSchedulerService()

        # Set with admin user (should succeed)
        success = await service.set_builtin_task_active(
            admin_user,
            'cleanup_tournament_usage',
            False
        )

        assert success is True

        # Verify it's in the cache
        assert TaskSchedulerService._builtin_task_overrides.get('cleanup_tournament_usage') is False

    @pytest.mark.asyncio
    async def test_reload_builtin_task_overrides(self, db):
        """Test reloading overrides from database."""
        repo = BuiltinTaskOverrideRepository()

        # Create some overrides in database
        await repo.create(task_id='reload_task_1', is_active=False)
        await repo.create(task_id='reload_task_2', is_active=True)

        # Clear cache and reload
        TaskSchedulerService.clear_builtin_task_overrides_cache()
        await TaskSchedulerService.reload_builtin_task_overrides()

        # Verify effective status reflects database values
        assert TaskSchedulerService.get_effective_active_status('reload_task_1', True) is False
        assert TaskSchedulerService.get_effective_active_status('reload_task_2', False) is True
