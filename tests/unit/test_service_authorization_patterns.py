"""
Unit tests for service layer authorization patterns.

These tests verify that service methods properly enforce authorization
through various patterns (permission checks, membership checks, ownership checks, etc.).
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from models import User, Permission
from application.services.core.user_service import UserService
from application.services.notifications.notification_service import NotificationService
from application.services.randomizer.preset_namespace_service import PresetNamespaceService
from application.services.tournaments.tournament_usage_service import TournamentUsageService


@pytest.mark.unit
@pytest.mark.asyncio
class TestGlobalPermissionChecks:
    """Test services that check global permissions (ADMIN, MODERATOR, SUPERADMIN)."""

    async def test_get_all_users_requires_admin(self):
        """Test that get_all_users requires ADMIN permission."""
        service = UserService()
        
        # Mock repository
        service.user_repository = AsyncMock()
        service.user_repository.get_all = AsyncMock(return_value=[])
        
        # Create users with different permissions
        regular_user = User(id=1, discord_id=123, discord_username="regular", permission=Permission.USER, is_active=True)
        moderator = User(id=2, discord_id=124, discord_username="mod", permission=Permission.MODERATOR, is_active=True)
        admin = User(id=3, discord_id=125, discord_username="admin", permission=Permission.ADMIN, is_active=True)
        
        # Regular user should get empty list
        result = await service.get_all_users(regular_user)
        assert result == []
        
        # Moderator should get empty list (needs ADMIN, not MODERATOR)
        result = await service.get_all_users(moderator)
        assert result == []
        
        # Admin should get results
        result = await service.get_all_users(admin)
        service.user_repository.get_all.assert_called_once()
    
    async def test_search_users_requires_moderator(self):
        """Test that search_users requires MODERATOR permission."""
        service = UserService()
        
        # Mock repository
        service.user_repository = AsyncMock()
        service.user_repository.search_by_username = AsyncMock(return_value=[])
        
        # Create users
        regular_user = User(id=1, discord_id=123, discord_username="regular", permission=Permission.USER, is_active=True)
        moderator = User(id=2, discord_id=124, discord_username="mod", permission=Permission.MODERATOR, is_active=True)
        
        # Regular user should get empty list
        result = await service.search_users(regular_user, "test")
        assert result == []
        
        # Moderator should get results
        result = await service.search_users(moderator, "test")
        service.user_repository.search_by_username.assert_called_once_with("test")


@pytest.mark.unit
@pytest.mark.asyncio
class TestUserScopedAuthorization:
    """Test services that use user-scoped authorization (implicit through query filtering)."""

    async def test_notification_subscribe_is_user_scoped(self):
        """Test that subscribe creates subscription for the authenticated user only."""
        service = NotificationService()
        
        # Mock repository
        service.repository = AsyncMock()
        service.repository.get_user_subscriptions = AsyncMock(return_value=[])
        service.repository.create_subscription = AsyncMock()
        
        # Create user
        user = User(id=1, discord_id=123, discord_username="testuser", permission=Permission.USER, is_active=True)
        
        # Subscribe
        from models import NotificationEventType, NotificationMethod
        await service.subscribe(user, NotificationEventType.TOURNAMENT_CREATED, NotificationMethod.DISCORD_DM)
        
        # Verify repository was called with user.id
        service.repository.get_user_subscriptions.assert_called_once()
        args = service.repository.get_user_subscriptions.call_args
        assert args.kwargs['user_id'] == user.id
    
    async def test_get_user_subscriptions_is_user_scoped(self):
        """Test that get_user_subscriptions queries by user.id."""
        service = NotificationService()
        
        # Mock repository
        service.repository = AsyncMock()
        service.repository.get_user_subscriptions = AsyncMock(return_value=[])
        
        # Create user
        user = User(id=1, discord_id=123, discord_username="testuser", permission=Permission.USER, is_active=True)
        
        # Get subscriptions
        await service.get_user_subscriptions(user)
        
        # Verify repository was called with user.id
        service.repository.get_user_subscriptions.assert_called_once()
        args = service.repository.get_user_subscriptions.call_args
        assert args.kwargs['user_id'] == user.id
    
    async def test_toggle_subscription_verifies_ownership(self):
        """Test that toggle_subscription verifies user owns the subscription."""
        service = NotificationService()
        
        # Create users
        user1 = User(id=1, discord_id=123, discord_username="user1", permission=Permission.USER, is_active=True)
        user2 = User(id=2, discord_id=124, discord_username="user2", permission=Permission.USER, is_active=True)
        
        # Mock subscription owned by user1
        mock_subscription = MagicMock()
        mock_subscription.user_id = 1
        mock_subscription.is_active = True
        
        # Mock repository
        service.repository = AsyncMock()
        service.repository.get_subscription_by_id = AsyncMock(return_value=mock_subscription)
        service.repository.update_subscription = AsyncMock()
        
        # User1 should be able to toggle their own subscription
        result = await service.toggle_subscription(1, user1)
        assert result is not None
        service.repository.update_subscription.assert_called_once()
        
        # Reset mock
        service.repository.update_subscription.reset_mock()
        
        # User2 should NOT be able to toggle user1's subscription
        result = await service.toggle_subscription(1, user2)
        assert result is None
        service.repository.update_subscription.assert_not_called()


@pytest.mark.unit
@pytest.mark.asyncio
class TestPresetNamespaceAuthorization:
    """Test preset namespace service authorization."""

    async def test_create_namespace_is_user_scoped(self):
        """Test that create_namespace creates namespace for the authenticated user."""
        service = PresetNamespaceService()
        
        # Mock repository methods
        service.repository = AsyncMock()
        service.repository.get_by_name = AsyncMock(return_value=None)
        service.repository.create_user_namespace = AsyncMock()
        
        # Create user
        user = User(id=1, discord_id=123, discord_username="testuser", permission=Permission.USER, is_active=True)
        
        # Create namespace
        await service.create_namespace(user, "test-namespace")
        
        # Verify repository was called with the user
        service.repository.create_user_namespace.assert_called_once()
        args = service.repository.create_user_namespace.call_args
        assert args.kwargs['user'] == user


@pytest.mark.unit
@pytest.mark.asyncio
class TestTournamentUsageAuthorization:
    """Test tournament usage service authorization."""

    async def test_get_recent_tournaments_is_user_scoped(self):
        """Test that get_recent_tournaments queries only the user's tournaments."""
        service = TournamentUsageService()
        
        # Mock repository
        service.repository = AsyncMock()
        service.repository.get_recent_tournaments = AsyncMock(return_value=[])
        
        # Create user
        user = User(id=1, discord_id=123, discord_username="testuser", permission=Permission.USER, is_active=True)
        
        # Get recent tournaments
        await service.get_recent_tournaments(user, limit=5)
        
        # Verify repository was called with the user
        service.repository.get_recent_tournaments.assert_called_once()
        args = service.repository.get_recent_tournaments.call_args
        assert args.args[0] == user


@pytest.mark.unit
@pytest.mark.asyncio
class TestAuthorizationReturnPatterns:
    """Test that unauthorized access returns empty results instead of raising exceptions."""

    async def test_get_all_users_returns_empty_on_unauthorized(self):
        """Test that get_all_users returns empty list for unauthorized users."""
        service = UserService()
        
        # Mock repository (should not be called)
        service.user_repository = AsyncMock()
        service.user_repository.get_all = AsyncMock(return_value=[])
        
        # Create regular user
        user = User(id=1, discord_id=123, discord_username="regular", permission=Permission.USER, is_active=True)
        
        # Get all users - should return empty list, not raise exception
        result = await service.get_all_users(user)
        
        assert result == []
        # Repository should NOT be called for unauthorized user
        service.user_repository.get_all.assert_not_called()
    
    async def test_search_users_returns_empty_on_unauthorized(self):
        """Test that search_users returns empty list for unauthorized users."""
        service = UserService()
        
        # Mock repository (should not be called)
        service.user_repository = AsyncMock()
        service.user_repository.search_by_username = AsyncMock(return_value=[])
        
        # Create regular user
        user = User(id=1, discord_id=123, discord_username="regular", permission=Permission.USER, is_active=True)
        
        # Search users - should return empty list, not raise exception
        result = await service.search_users(user, "test")
        
        assert result == []
        # Repository should NOT be called for unauthorized user
        service.user_repository.search_by_username.assert_not_called()
