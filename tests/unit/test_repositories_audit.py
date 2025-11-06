"""
Unit tests for AuditRepository.

Tests the data access layer for AuditLog operations.
"""

import pytest
from application.repositories.audit_repository import AuditRepository


@pytest.mark.unit
@pytest.mark.asyncio
class TestAuditRepository:
    """Test cases for AuditRepository."""
    
    async def test_create_audit_log(self, sample_user):
        """Test creating an audit log entry."""
        repo = AuditRepository()
        
        log = await repo.create(
            user=sample_user,
            action="test_action",
            details={"key": "value"},
            ip_address="127.0.0.1"
        )
        
        # Verify log was created
        assert log.id is not None
        assert log.user_id == sample_user.id
        assert log.action == "test_action"
        assert log.details == {"key": "value"}
        assert log.ip_address == "127.0.0.1"
    
    async def test_get_user_audit_logs(self, sample_user):
        """Test retrieving audit logs for a user."""
        repo = AuditRepository()
        
        # Create multiple logs for the user
        await repo.create(user=sample_user, action="action1")
        await repo.create(user=sample_user, action="action2")
        await repo.create(user=sample_user, action="action3")
        
        # Create log for different user
        from models.user import User, Permission
        other_user = await User.create(
            discord_id=999999999999999999,
            discord_username="other_user",
            permission=Permission.USER
        )
        await repo.create(user=other_user, action="other_action")
        
        # Get logs for sample_user
        logs = await repo.get_by_user(sample_user.id, limit=10)
        
        # Verify only sample_user's logs are returned
        assert len(logs) == 3
        for log in logs:
            assert log.user_id == sample_user.id
    
    async def test_get_recent_audit_logs(self, sample_user):
        """Test retrieving recent audit logs."""
        repo = AuditRepository()
        
        # Create multiple logs
        await repo.create(user=sample_user, action="action1")
        await repo.create(user=sample_user, action="action2")
        await repo.create(user=sample_user, action="action3")
        
        # Get recent logs with limit
        logs = await repo.get_recent(limit=2)
        
        # Verify limit is respected
        assert len(logs) == 2
        
        # Verify logs are ordered by most recent first
        assert logs[0].action == "action3"
        assert logs[1].action == "action2"
    
    async def test_get_recent_for_org(self, sample_user, sample_organization):
        """Test retrieving recent audit logs for an organization."""
        repo = AuditRepository()
        
        # Create logs for organization
        await repo.create(
            user=sample_user,
            action="org_action1",
            organization_id=sample_organization.id
        )
        await repo.create(
            user=sample_user,
            action="org_action2",
            organization_id=sample_organization.id
        )
        
        # Create log without organization
        await repo.create(user=sample_user, action="global_action")
        
        # Get org-specific logs
        logs = await repo.get_recent_for_org(sample_organization.id, limit=10)
        
        # Verify only org logs are returned
        assert len(logs) == 2
        for log in logs:
            assert log.organization_id == sample_organization.id
    
    async def test_get_by_user_in_org(self, sample_user, sample_organization):
        """Test retrieving audit logs for a user in a specific organization."""
        repo = AuditRepository()
        
        # Create user logs in organization
        await repo.create(
            user=sample_user,
            action="user_org_action1",
            organization_id=sample_organization.id
        )
        await repo.create(
            user=sample_user,
            action="user_org_action2",
            organization_id=sample_organization.id
        )
        
        # Create user log in different context
        await repo.create(user=sample_user, action="user_global_action")
        
        # Create other user log in same org
        from models.user import User, Permission
        other_user = await User.create(
            discord_id=888888888888888888,
            discord_username="other_user",
            permission=Permission.USER
        )
        await repo.create(
            user=other_user,
            action="other_user_org_action",
            organization_id=sample_organization.id
        )
        
        # Get logs for sample_user in organization
        logs = await repo.get_by_user_in_org(
            sample_user.id,
            sample_organization.id,
            limit=10
        )
        
        # Verify filtering
        assert len(logs) == 2
        for log in logs:
            assert log.user_id == sample_user.id
            assert log.organization_id == sample_organization.id
    
    async def test_create_with_null_user(self, db):
        """Test creating audit log without user (unauthenticated action)."""
        repo = AuditRepository()
        
        log = await repo.create(
            user=None,
            action="anonymous_action",
            ip_address="192.168.1.1"
        )
        
        assert log.id is not None
        assert log.user_id is None
        assert log.action == "anonymous_action"
