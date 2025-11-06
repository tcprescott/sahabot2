"""
Unit tests for UserRepository.

Tests the data access layer for User operations.
"""

import pytest
from application.repositories.user_repository import UserRepository
from models.user import Permission


@pytest.mark.unit
@pytest.mark.asyncio
class TestUserRepository:
    """Test cases for UserRepository."""
    
    async def test_get_all_users(self, db):
        """Test retrieving all users."""
        repo = UserRepository()
        
        # Create multiple users
        from models.user import User
        await User.create(
            discord_id=111111111111111111,
            discord_username="user1",
            permission=Permission.USER,
            is_active=True
        )
        await User.create(
            discord_id=222222222222222222,
            discord_username="user2",
            permission=Permission.USER,
            is_active=True
        )
        
        # Create inactive user
        await User.create(
            discord_id=333333333333333333,
            discord_username="inactive",
            permission=Permission.USER,
            is_active=False
        )
        
        # Get all active users
        users = await repo.get_all(include_inactive=False)
        assert len(users) == 2
        
        # Get all users including inactive
        all_users = await repo.get_all(include_inactive=True)
        assert len(all_users) == 3
    
    async def test_get_user_by_id(self, sample_user):
        """Test retrieving user by ID."""
        repo = UserRepository()
        
        user = await repo.get_by_id(sample_user.id)
        
        assert user is not None
        assert user.id == sample_user.id
        assert user.discord_username == sample_user.discord_username
        
        # Test non-existent user
        not_found = await repo.get_by_id(999999)
        assert not_found is None
    
    async def test_get_user_by_discord_id(self, sample_user):
        """Test retrieving user by Discord ID."""
        repo = UserRepository()
        
        user = await repo.get_by_discord_id(sample_user.discord_id)
        
        assert user is not None
        assert user.discord_id == sample_user.discord_id
        assert user.id == sample_user.id
        
        # Test non-existent discord ID
        not_found = await repo.get_by_discord_id(999999999999999999)
        assert not_found is None
    
    async def test_create_user(self, db, discord_user_payload):
        """Test creating a new user."""
        repo = UserRepository()
        
        user = await repo.create(
            discord_id=int(discord_user_payload["id"]),
            discord_username=discord_user_payload["username"],
            discord_discriminator=discord_user_payload["discriminator"],
            discord_avatar=discord_user_payload["avatar"],
            permission=Permission.USER
        )
        
        assert user.id is not None
        assert user.discord_id == int(discord_user_payload["id"])
        assert user.discord_username == discord_user_payload["username"]
        assert user.permission == Permission.USER
        assert user.is_active is True
    
    async def test_update_user(self, sample_user):
        """Test updating user data."""
        # Update username directly on model
        sample_user.discord_username = "updated_username"
        await sample_user.save()
        
        # Fetch and verify update
        repo = UserRepository()
        updated_user = await repo.get_by_id(sample_user.id)
        
        assert updated_user.discord_username == "updated_username"
    
    async def test_delete_user(self, sample_user):
        """Test deleting a user."""
        user_id = sample_user.id
        
        # Delete user
        await sample_user.delete()
        
        # Verify deletion
        repo = UserRepository()
        deleted_user = await repo.get_by_id(user_id)
        
        assert deleted_user is None
    
    async def test_search_by_username(self, db):
        """Test searching users by username."""
        repo = UserRepository()
        
        # Create users with different names
        from models.user import User
        await User.create(
            discord_id=111111111111111111,
            discord_username="alice",
            permission=Permission.USER,
            is_active=True
        )
        await User.create(
            discord_id=222222222222222222,
            discord_username="bob",
            permission=Permission.USER,
            is_active=True
        )
        await User.create(
            discord_id=333333333333333333,
            discord_username="alice_wonderland",
            permission=Permission.USER,
            is_active=True
        )
        
        # Search for "alice"
        results = await repo.search_by_username("alice")
        
        # Should find both users with "alice" in username
        assert len(results) == 2
        usernames = [u.discord_username for u in results]
        assert "alice" in usernames
        assert "alice_wonderland" in usernames
    
    async def test_get_admins(self, db):
        """Test retrieving admin users."""
        repo = UserRepository()
        
        # Create users with different permissions
        from models.user import User
        await User.create(
            discord_id=111111111111111111,
            discord_username="user",
            permission=Permission.USER,
            is_active=True
        )
        await User.create(
            discord_id=222222222222222222,
            discord_username="admin",
            permission=Permission.ADMIN,
            is_active=True
        )
        await User.create(
            discord_id=333333333333333333,
            discord_username="superadmin",
            permission=Permission.SUPERADMIN,
            is_active=True
        )
        
        # Get admins (ADMIN and above)
        admins = await repo.get_admins()
        
        assert len(admins) == 2
        permissions = [u.permission for u in admins]
        assert Permission.ADMIN in permissions
        assert Permission.SUPERADMIN in permissions
    
    async def test_count_active_users(self, db):
        """Test counting active users."""
        repo = UserRepository()
        
        # Create users
        from models.user import User
        await User.create(
            discord_id=111111111111111111,
            discord_username="user1",
            permission=Permission.USER,
            is_active=True
        )
        await User.create(
            discord_id=222222222222222222,
            discord_username="user2",
            permission=Permission.USER,
            is_active=True
        )
        await User.create(
            discord_id=333333333333333333,
            discord_username="inactive",
            permission=Permission.USER,
            is_active=False
        )
        
        count = await repo.count_active_users()
        assert count == 2
    
    async def test_get_by_racetime_id(self, sample_user):
        """Test retrieving user by RaceTime ID."""
        repo = UserRepository()
        
        # Set racetime_id on user
        sample_user.racetime_id = "test_racetime_123"
        await sample_user.save()
        
        # Find by racetime_id
        user = await repo.get_by_racetime_id("test_racetime_123")
        
        assert user is not None
        assert user.id == sample_user.id
        assert user.racetime_id == "test_racetime_123"
        
        # Test non-existent racetime_id
        not_found = await repo.get_by_racetime_id("nonexistent_id")
        assert not_found is None
