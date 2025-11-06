"""
Integration tests for database operations.

Tests database operations across models and relationships.
"""

import pytest
import asyncio
from models.user import User
from models.audit_log import AuditLog
from models.organizations import Organization
from tortoise.exceptions import IntegrityError
from tortoise.transactions import in_transaction


@pytest.mark.integration
@pytest.mark.asyncio
class TestDatabaseIntegration:
    """Test cases for database integration."""
    
    async def test_user_audit_log_relationship(self, sample_user):
        """Test relationship between User and AuditLog models."""
        # Create audit logs for user
        log1 = await AuditLog.create(
            user=sample_user,
            action="test_action_1",
            ip_address="127.0.0.1"
        )
        log2 = await AuditLog.create(
            user=sample_user,
            action="test_action_2",
            ip_address="127.0.0.1"
        )
        
        # Fetch user with prefetched audit logs
        user_with_logs = await User.filter(id=sample_user.id).prefetch_related('audit_logs').first()
        
        # Verify relationship
        assert user_with_logs is not None
        audit_logs = await user_with_logs.audit_logs.all()
        assert len(audit_logs) == 2
        assert any(log.id == log1.id for log in audit_logs)
        assert any(log.id == log2.id for log in audit_logs)
        
        # Verify reverse relationship
        fetched_log1 = await AuditLog.filter(id=log1.id).prefetch_related('user').first()
        assert fetched_log1.user.id == sample_user.id
    
    async def test_cascade_delete_behavior(self, sample_user, sample_organization):
        """Test cascade delete behavior."""
        # Create audit log linked to user
        audit_log = await AuditLog.create(
            user=sample_user,
            action="test_action",
            ip_address="127.0.0.1"
        )
        
        audit_log_id = audit_log.id
        user_id = sample_user.id
        
        # Delete user
        await sample_user.delete()
        
        # Verify user is deleted
        deleted_user = await User.filter(id=user_id).first()
        assert deleted_user is None
        
        # Check if audit log was cascade deleted or set to null
        # (behavior depends on database ForeignKey configuration)
        remaining_log = await AuditLog.filter(id=audit_log_id).first()
        
        # Either: audit log deleted (CASCADE) OR user_id set to null (SET NULL)
        if remaining_log is None:
            # CASCADE behavior - audit log was deleted
            assert True  # Test passes - cascade delete worked
        else:
            # SET NULL behavior - audit log remains but user is null
            assert remaining_log.user_id is None
    
    async def test_transaction_rollback(self, db):
        """Test transaction rollback on error."""
        # Count users before transaction
        initial_count = await User.all().count()
        
        # Attempt to create users in a transaction with an error
        try:
            async with in_transaction():
                # Create valid user
                await User.create(
                    discord_id=999888777,
                    discord_username="transaction_test_user"
                )
                
                # Raise an error to trigger rollback
                raise ValueError("Intentional error for rollback test")
        except ValueError:
            pass  # Expected error
        
        # Verify user was rolled back
        final_count = await User.all().count()
        assert final_count == initial_count
        
        # Verify user was not created
        user = await User.filter(discord_id=999888777).first()
        assert user is None
    
    async def test_concurrent_operations(self, db):
        """Test handling concurrent database operations."""
        # Create unique discord IDs for concurrent users
        discord_ids = [111111111 + i for i in range(5)]
        
        # Create users concurrently
        async def create_user(discord_id):
            return await User.create(
                discord_id=discord_id,
                discord_username=f"concurrent_user_{discord_id}"
            )
        
        # Execute concurrent creates
        users = await asyncio.gather(*[create_user(did) for did in discord_ids])
        
        # Verify all users were created
        assert len(users) == 5
        assert all(user.id is not None for user in users)
        
        # Verify unique constraint works (discord_id must be unique)
        with pytest.raises(IntegrityError):
            await User.create(
                discord_id=discord_ids[0],  # Duplicate
                discord_username="duplicate_user"
            )
        
        # Clean up
        for user in users:
            await user.delete()
