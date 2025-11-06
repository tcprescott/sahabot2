"""
Integration tests for user management workflows.

Tests complete user management scenarios.
"""

import pytest
from models.user import User, Permission
from models.audit_log import AuditLog
from application.services.core.user_service import UserService
from application.services.core.audit_service import AuditService


@pytest.mark.integration
@pytest.mark.asyncio
class TestUserManagementWorkflow:
    """Test cases for user management workflows."""
    
    async def test_create_and_retrieve_user(self, db, discord_user_payload):
        """Test creating and retrieving a user."""
        # Create user service
        user_service = UserService()
        
        # Create user from Discord OAuth data
        user = await user_service.get_or_create_user_from_discord(
            discord_id=discord_user_payload['id'],
            discord_username=discord_user_payload['username'],
            discord_discriminator=discord_user_payload['discriminator'],
            discord_avatar=discord_user_payload['avatar']
        )
        
        # Verify user was created
        assert user is not None
        assert user.id is not None
        assert user.discord_id == int(discord_user_payload['id'])
        assert user.discord_username == discord_user_payload['username']
        assert user.permission == Permission.USER
        assert user.is_active is True
        
        # Retrieve user by ID
        retrieved = await user_service.get_user_by_id(user.id)
        assert retrieved is not None
        assert retrieved.id == user.id
        assert retrieved.discord_id == user.discord_id
        
        # Call again with same Discord ID (should return existing user)
        existing = await user_service.get_or_create_user_from_discord(
            discord_id=discord_user_payload['id'],
            discord_username=discord_user_payload['username'],
            discord_discriminator=discord_user_payload['discriminator'],
            discord_avatar=discord_user_payload['avatar']
        )
        assert existing.id == user.id
    
    async def test_update_user_permission_workflow(self, sample_user, admin_user):
        """Test complete permission update workflow."""
        # Initial permission should be USER
        assert sample_user.permission == Permission.USER
        
        # Create user service
        user_service = UserService()
        
        # Update permission to MODERATOR
        updated_user = await user_service.update_user_permission(
            user_id=sample_user.id,
            new_permission=Permission.MODERATOR,
            acting_user_id=admin_user.id
        )
        
        # Verify permission was updated
        assert updated_user is not None
        assert updated_user.permission == Permission.MODERATOR
        
        # Verify in database
        db_user = await User.filter(id=sample_user.id).first()
        assert db_user.permission == Permission.MODERATOR
        
        # Update to ADMIN
        updated_user = await user_service.update_user_permission(
            user_id=sample_user.id,
            new_permission=Permission.ADMIN,
            acting_user_id=admin_user.id
        )
        
        # Verify second update
        assert updated_user.permission == Permission.ADMIN
        db_user = await User.filter(id=sample_user.id).first()
        assert db_user.permission == Permission.ADMIN
    
    async def test_user_deactivation_workflow(self, sample_user):
        """Test deactivating a user."""
        # User should start active
        assert sample_user.is_active is True
        
        # Create user service
        user_service = UserService()
        
        # Deactivate user
        deactivated = await user_service.deactivate_user(sample_user.id)
        
        # Verify user was deactivated
        assert deactivated is not None
        assert deactivated.is_active is False
        
        # Verify in database
        db_user = await User.filter(id=sample_user.id).first()
        assert db_user.is_active is False
        
        # Reactivate user
        reactivated = await user_service.activate_user(sample_user.id)
        
        # Verify user was reactivated
        assert reactivated is not None
        assert reactivated.is_active is True
        
        # Verify in database
        db_user = await User.filter(id=sample_user.id).first()
        assert db_user.is_active is True
    
    async def test_audit_log_creation_on_user_action(self, sample_user):
        """Test audit log is created when user performs action."""
        # Create audit service
        audit_service = AuditService()
        
        # Count existing audit logs
        initial_count = await AuditLog.all().count()
        
        # Log a user action
        await audit_service.log_action(
            user=sample_user,
            action="test_user_action",
            details={"test_key": "test_value"},
            ip_address="192.168.1.1"
        )
        
        # Verify audit log was created
        final_count = await AuditLog.all().count()
        assert final_count == initial_count + 1
        
        # Retrieve the log
        log = await AuditLog.filter(
            action="test_user_action"
        ).order_by('-created_at').first()
        
        assert log is not None
        assert log.user_id == sample_user.id
        assert log.action == "test_user_action"
        assert log.ip_address == "192.168.1.1"
        assert log.details is not None
        assert log.details.get("test_key") == "test_value"
        
        # Verify relationship
        await log.fetch_related('user')
        assert log.user.id == sample_user.id
        assert log.user.discord_username == sample_user.discord_username
