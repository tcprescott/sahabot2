"""
Unit tests for AuditLog model.

Tests the AuditLog model functionality.
"""

import pytest
from models.audit_log import AuditLog


@pytest.mark.unit
@pytest.mark.asyncio
class TestAuditLogModel:
    """Test cases for the AuditLog model."""

    async def test_create_audit_log(self, sample_user):
        """Test creating an audit log entry."""
        # Create audit log
        log = await AuditLog.create(
            user=sample_user,
            action="test_action",
            details={"key": "value"},
            ip_address="127.0.0.1",
        )

        # Verify fields
        assert log.id is not None
        assert log.user_id == sample_user.id
        assert log.action == "test_action"
        assert log.details == {"key": "value"}
        assert log.ip_address == "127.0.0.1"
        assert log.created_at is not None

    async def test_audit_log_details_json(self, sample_user):
        """Test JSON details field."""
        # Create audit log with complex JSON
        complex_details = {
            "target_id": 123,
            "old_value": "old",
            "new_value": "new",
            "nested": {"foo": "bar"},
        }

        log = await AuditLog.create(
            user=sample_user, action="update_action", details=complex_details
        )

        # Fetch and verify JSON is preserved
        fetched_log = await AuditLog.get(id=log.id)
        assert fetched_log.details == complex_details
        assert fetched_log.details["nested"]["foo"] == "bar"

    async def test_audit_log_relationship(self, sample_user):
        """Test relationship with User model."""
        # Create audit log
        log = await AuditLog.create(user=sample_user, action="test_action")

        # Fetch with relationship
        fetched_log = await AuditLog.get(id=log.id).prefetch_related("user")

        # Verify relationship
        assert fetched_log.user is not None
        assert fetched_log.user.id == sample_user.id
        assert fetched_log.user.discord_username == sample_user.discord_username

    async def test_audit_log_without_user(self, db):
        """Test creating audit log without user (for unauthenticated actions)."""
        log = await AuditLog.create(
            user=None, action="anonymous_action", ip_address="192.168.1.1"
        )

        assert log.id is not None
        assert log.user_id is None
        assert log.action == "anonymous_action"

    async def test_audit_log_with_organization(self, sample_user, sample_organization):
        """Test audit log with organization context."""
        log = await AuditLog.create(
            user=sample_user,
            organization=sample_organization,
            action="org_action",
            details={"org_id": sample_organization.id},
        )

        assert log.organization_id == sample_organization.id

        # Fetch with relationships
        fetched_log = await AuditLog.get(id=log.id).prefetch_related("organization")
        assert fetched_log.organization.name == "Test Organization"

    async def test_audit_log_str_representation(self, sample_user):
        """Test string representation of audit log."""
        log = await AuditLog.create(user=sample_user, action="test_action")

        log_str = str(log)
        assert "test_action" in log_str
        assert log.user is not None  # Will be fetched if needed
