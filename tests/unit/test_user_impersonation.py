"""
Test user impersonation feature.

This module tests the user impersonation functionality including permissions,
session management, and audit logging.
"""

import pytest
from models import User, Permission
from application.services.core.user_service import UserService
from middleware.auth import DiscordAuthService
from nicegui import app


@pytest.mark.asyncio
class TestUserImpersonation:
    """Test user impersonation feature."""

    async def test_superadmin_can_start_impersonation(self, db):
        """Test that SUPERADMIN can start impersonation."""
        # Create users
        service = UserService()
        
        # Create SUPERADMIN
        admin_user = await service.create_user_manual(
            discord_id=111111,
            discord_username="admin_user",
            permission=Permission.SUPERADMIN
        )
        
        # Create regular user
        target_user = await service.create_user_manual(
            discord_id=222222,
            discord_username="target_user",
            permission=Permission.USER
        )
        
        # Start impersonation
        result = await service.start_impersonation(
            admin_user=admin_user,
            target_user_id=target_user.id,
            ip_address="127.0.0.1"
        )
        
        # Should succeed
        assert result is not None
        assert result.id == target_user.id
        assert result.discord_username == "target_user"

    async def test_admin_cannot_impersonate(self, db):
        """Test that ADMIN (non-SUPERADMIN) cannot impersonate."""
        service = UserService()
        
        # Create ADMIN (not SUPERADMIN)
        admin_user = await service.create_user_manual(
            discord_id=111111,
            discord_username="admin_user",
            permission=Permission.ADMIN  # Not SUPERADMIN
        )
        
        # Create regular user
        target_user = await service.create_user_manual(
            discord_id=222222,
            discord_username="target_user",
            permission=Permission.USER
        )
        
        # Attempt impersonation
        result = await service.start_impersonation(
            admin_user=admin_user,
            target_user_id=target_user.id,
            ip_address="127.0.0.1"
        )
        
        # Should fail
        assert result is None

    async def test_cannot_impersonate_self(self, db):
        """Test that users cannot impersonate themselves."""
        service = UserService()
        
        # Create SUPERADMIN
        admin_user = await service.create_user_manual(
            discord_id=111111,
            discord_username="admin_user",
            permission=Permission.SUPERADMIN
        )
        
        # Attempt self-impersonation
        result = await service.start_impersonation(
            admin_user=admin_user,
            target_user_id=admin_user.id,  # Same user!
            ip_address="127.0.0.1"
        )
        
        # Should fail
        assert result is None

    async def test_cannot_impersonate_nonexistent_user(self, db):
        """Test that impersonating non-existent user fails."""
        service = UserService()
        
        # Create SUPERADMIN
        admin_user = await service.create_user_manual(
            discord_id=111111,
            discord_username="admin_user",
            permission=Permission.SUPERADMIN
        )
        
        # Attempt to impersonate non-existent user
        result = await service.start_impersonation(
            admin_user=admin_user,
            target_user_id=99999,  # Doesn't exist
            ip_address="127.0.0.1"
        )
        
        # Should fail
        assert result is None

    async def test_impersonation_audit_logging(self, db):
        """Test that impersonation creates audit log entries."""
        service = UserService()
        
        # Create SUPERADMIN
        admin_user = await service.create_user_manual(
            discord_id=111111,
            discord_username="admin_user",
            permission=Permission.SUPERADMIN
        )
        
        # Create regular user
        target_user = await service.create_user_manual(
            discord_id=222222,
            discord_username="target_user",
            permission=Permission.USER
        )
        
        # Start impersonation
        await service.start_impersonation(
            admin_user=admin_user,
            target_user_id=target_user.id,
            ip_address="127.0.0.1"
        )
        
        # Check audit logs
        from application.services.core.audit_service import AuditService
        audit_service = AuditService()
        logs = await audit_service.get_user_logs(admin_user.id, limit=10)
        
        # Should have an impersonation_started entry
        start_logs = [log for log in logs if log.action == "impersonation_started"]
        assert len(start_logs) > 0
        
        start_log = start_logs[0]
        assert start_log.details["target_user_id"] == target_user.id
        assert start_log.details["target_username"] == "target_user"
        assert start_log.ip_address == "127.0.0.1"
        
        # Stop impersonation
        await service.stop_impersonation(
            original_user=admin_user,
            impersonated_user=target_user,
            ip_address="127.0.0.1"
        )
        
        # Check for stop log
        logs = await audit_service.get_user_logs(admin_user.id, limit=10)
        stop_logs = [log for log in logs if log.action == "impersonation_stopped"]
        assert len(stop_logs) > 0
        
        stop_log = stop_logs[0]
        assert stop_log.details["impersonated_user_id"] == target_user.id
        assert stop_log.details["impersonated_username"] == "target_user"


# Note: Session-based tests require NiceGUI app context and are better tested manually
# These tests focus on the service layer business logic
