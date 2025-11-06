"""
Unit tests for UserService.

Tests the business logic layer for User operations.
"""

import pytest
from unittest.mock import AsyncMock, patch
from application.services.core.user_service import UserService
from models.user import Permission, User


@pytest.mark.unit
@pytest.mark.asyncio
class TestUserService:
    """Test cases for UserService."""
    
    async def test_get_all_users(self, admin_user):
        """Test retrieving all users (admin only)."""
        service = UserService()
        
        # Mock repository
        mock_users = [
            User(id=1, discord_id=111, discord_username="user1", permission=Permission.USER, is_active=True),
            User(id=2, discord_id=222, discord_username="user2", permission=Permission.USER, is_active=True)
        ]
        service.user_repository.get_all = AsyncMock(return_value=mock_users)
        
        # Call service
        users = await service.get_all_users(admin_user)
        
        # Verify
        service.user_repository.get_all.assert_called_once()
        assert len(users) == 2
        assert users[0].discord_username == "user1"
    
    async def test_get_all_users_unauthorized(self, sample_user):
        """Test get_all_users returns empty for non-admin."""
        service = UserService()
        
        # Non-admin user
        users = await service.get_all_users(sample_user)
        
        # Should return empty list
        assert users == []
    
    async def test_get_user_by_id(self, sample_user):
        """Test retrieving user by ID."""
        service = UserService()
        
        # Mock repository
        service.user_repository.get_by_id = AsyncMock(return_value=sample_user)
        
        # Call service
        user = await service.get_user_by_id(sample_user.id)
        
        # Verify
        service.user_repository.get_by_id.assert_called_once_with(sample_user.id)
        assert user.id == sample_user.id
    
    @patch('application.services.core.user_service.EventBus')
    async def test_create_user_from_discord(self, mock_event_bus, discord_user_payload):
        """Test creating user from Discord data."""
        service = UserService()
        
        # Mock repository - user doesn't exist yet
        service.user_repository.get_by_discord_id = AsyncMock(return_value=None)
        
        new_user = User(
            id=1,
            discord_id=int(discord_user_payload["id"]),
            discord_username=discord_user_payload["username"],
            permission=Permission.USER,
            is_active=True
        )
        service.user_repository.create = AsyncMock(return_value=new_user)
        
        # Mock event emission
        mock_event_bus.emit = AsyncMock()
        
        # Call service
        user = await service.get_or_create_user_from_discord(
            discord_id=int(discord_user_payload["id"]),
            discord_username=discord_user_payload["username"],
            discord_discriminator=discord_user_payload["discriminator"],
            discord_avatar=discord_user_payload["avatar"]
        )
        
        # Verify repository create was called
        service.user_repository.create.assert_called_once()
        call_kwargs = service.user_repository.create.call_args.kwargs
        assert call_kwargs["discord_id"] == int(discord_user_payload["id"])
        assert call_kwargs["discord_username"] == discord_user_payload["username"]
        
        # Verify event was emitted
        mock_event_bus.emit.assert_called_once()
        event = mock_event_bus.emit.call_args.args[0]
        assert event.entity_id == new_user.id
        assert event.discord_id == new_user.discord_id
    
    @patch('application.services.core.user_service.EventBus')
    async def test_update_user_permission(self, mock_event_bus, sample_user, admin_user):
        """Test updating user permission."""
        service = UserService()
        
        # Mock repository
        service.user_repository.get_by_id = AsyncMock(return_value=sample_user)
        
        # Mock event emission
        mock_event_bus.emit = AsyncMock()
        
        # Update permission
        updated_user = await service.update_user_permission(
            user_id=sample_user.id,
            new_permission=Permission.ADMIN,
            acting_user_id=admin_user.id
        )
        
        # Verify user permission was updated
        assert updated_user is not None
        assert updated_user.permission == Permission.ADMIN
        
        # Verify event was emitted
        mock_event_bus.emit.assert_called_once()
        event = mock_event_bus.emit.call_args.args[0]
        assert event.entity_id == sample_user.id
        assert event.new_permission == Permission.ADMIN.name
    
    async def test_update_user_permission_not_found(self, admin_user):
        """Test permission update fails when user not found."""
        service = UserService()
        
        # Mock repository - user doesn't exist
        service.user_repository.get_by_id = AsyncMock(return_value=None)
        
        # Try to update - should raise ValueError
        with pytest.raises(ValueError, match="User with ID .* not found"):
            await service.update_user_permission(
                user_id=999999,
                new_permission=Permission.ADMIN,
                acting_user_id=admin_user.id
            )
    
    async def test_deactivate_user(self, sample_user):
        """Test deactivating a user."""
        service = UserService()
        
        # Mock repository
        service.user_repository.get_by_id = AsyncMock(return_value=sample_user)
        
        # Deactivate user
        deactivated_user = await service.deactivate_user(
            user_id=sample_user.id
        )
        
        # Verify user is deactivated
        assert deactivated_user is not None
        assert deactivated_user.is_active is False
    
    async def test_search_users(self, admin_user):
        """Test searching users by username."""
        service = UserService()
        
        # Mock repository
        mock_results = [
            User(id=1, discord_id=111, discord_username="alice", permission=Permission.USER, is_active=True),
            User(id=2, discord_id=222, discord_username="alice_wonderland", permission=Permission.USER, is_active=True)
        ]
        service.user_repository.search_by_username = AsyncMock(return_value=mock_results)
        
        # Search
        results = await service.search_users(query="alice", current_user=admin_user)
        
        # Verify
        service.user_repository.search_by_username.assert_called_once_with("alice")
        assert len(results) == 2
        assert results[0].discord_username == "alice"

