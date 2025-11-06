"""
Unit tests for AuditService.

Tests the business logic layer for audit logging.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock
from application.services.core.audit_service import AuditService
from models.audit_log import AuditLog


@pytest.mark.unit
@pytest.mark.asyncio
class TestAuditService:
    """Test cases for AuditService."""
    
    async def test_log_user_action(self, sample_user, sample_organization):
        """Test logging a user action with organization context."""
        service = AuditService()
        
        # Mock the repository
        mock_audit = AuditLog(
            id=1,
            user_id=sample_user.id,
            organization_id=sample_organization.id,
            action="test_action",
            details={"key": "value"},
            ip_address="127.0.0.1"
        )
        service.audit_repository.create = AsyncMock(return_value=mock_audit)
        
        # Log action
        result = await service.log_action(
            user=sample_user,
            action="test_action",
            details={"key": "value"},
            ip_address="127.0.0.1",
            organization_id=sample_organization.id
        )
        
        # Verify repository was called correctly
        service.audit_repository.create.assert_called_once()
        call_kwargs = service.audit_repository.create.call_args.kwargs
        assert call_kwargs["user"] == sample_user
        assert call_kwargs["action"] == "test_action"
        assert call_kwargs["details"] == {"key": "value"}
        assert call_kwargs["ip_address"] == "127.0.0.1"
        assert call_kwargs["organization_id"] == sample_organization.id
        
        # Verify return value
        assert result.id == 1
        assert result.action == "test_action"
    
    async def test_log_with_details(self, sample_user):
        """Test logging action with complex details dictionary."""
        service = AuditService()
        
        # Mock the repository
        complex_details = {
            "old_value": "foo",
            "new_value": "bar",
            "metadata": {
                "timestamp": "2025-11-05T12:00:00Z",
                "changed_by": "admin"
            }
        }
        mock_audit = AuditLog(
            id=2,
            user_id=sample_user.id,
            action="update_setting",
            details=complex_details
        )
        service.audit_repository.create = AsyncMock(return_value=mock_audit)
        
        # Log action with complex details
        result = await service.log_action(
            user=sample_user,
            action="update_setting",
            details=complex_details
        )
        
        # Verify details are preserved
        service.audit_repository.create.assert_called_once()
        call_kwargs = service.audit_repository.create.call_args.kwargs
        assert call_kwargs["details"] == complex_details
        
        assert result.details["old_value"] == "foo"
        assert result.details["new_value"] == "bar"
        assert result.details["metadata"]["changed_by"] == "admin"
    
    async def test_log_with_ip_address(self, sample_user):
        """Test logging action with IP address tracking."""
        service = AuditService()
        
        # Mock the repository
        mock_audit = AuditLog(
            id=3,
            user_id=sample_user.id,
            action="login",
            ip_address="192.168.1.100"
        )
        service.audit_repository.create = AsyncMock(return_value=mock_audit)
        
        # Log action with IP
        result = await service.log_action(
            user=sample_user,
            action="login",
            ip_address="192.168.1.100"
        )
        
        # Verify IP address is captured
        service.audit_repository.create.assert_called_once()
        call_kwargs = service.audit_repository.create.call_args.kwargs
        assert call_kwargs["ip_address"] == "192.168.1.100"
        
        assert result.ip_address == "192.168.1.100"
    
    async def test_log_login(self, sample_user):
        """Test specialized login logging method."""
        service = AuditService()
        
        # Mock the repository
        mock_audit = AuditLog(
            id=4,
            user_id=sample_user.id,
            action="user_login",
            details={"username": sample_user.discord_username},
            ip_address="10.0.0.1"
        )
        service.audit_repository.create = AsyncMock(return_value=mock_audit)
        
        # Log login
        result = await service.log_login(
            user=sample_user,
            ip_address="10.0.0.1"
        )
        
        # Verify correct action name
        service.audit_repository.create.assert_called_once()
        call_kwargs = service.audit_repository.create.call_args.kwargs
        assert call_kwargs["action"] == "user_login"
        assert call_kwargs["user"] == sample_user
        assert call_kwargs["ip_address"] == "10.0.0.1"
    
    async def test_log_permission_change(self, sample_user, admin_user):
        """Test specialized permission change logging."""
        service = AuditService()
        
        # Mock the repository
        from models.user import Permission
        mock_audit = AuditLog(
            id=5,
            user_id=admin_user.id,
            action="permission_change",
            details={
                "target_user_id": sample_user.id,
                "target_username": sample_user.discord_username,
                "old_permission": Permission.USER.value,
                "new_permission": Permission.ADMIN.value
            }
        )
        service.audit_repository.create = AsyncMock(return_value=mock_audit)
        
        # Log permission change
        result = await service.log_permission_change(
            admin_user=admin_user,
            target_user=sample_user,
            old_permission=Permission.USER.value,
            new_permission=Permission.ADMIN.value
        )
        
        # Verify details structure
        service.audit_repository.create.assert_called_once()
        call_kwargs = service.audit_repository.create.call_args.kwargs
        assert call_kwargs["action"] == "permission_change"
        assert call_kwargs["user"] == admin_user
        assert call_kwargs["details"]["target_user_id"] == sample_user.id
        assert call_kwargs["details"]["old_permission"] == Permission.USER.value
        assert call_kwargs["details"]["new_permission"] == Permission.ADMIN.value
