"""
Test notification subscription organization scoping.

Verifies that global and org-scoped subscriptions work correctly.
"""

import pytest
from models import User
from models.notification_subscription import NotificationEventType, NotificationMethod
from application.services.notification_service import NotificationService
from application.repositories.notification_repository import NotificationRepository


class TestNotificationOrganizationScoping:
    """Test organization scoping for notification subscriptions."""

    @pytest.fixture
    async def user(self):
        """Create a test user."""
        user = User(
            id=1,
            discord_id="123456789",
            discord_username="testuser",
            discord_discriminator="0001",
        )
        await user.save()
        return user

    @pytest.fixture
    def service(self):
        """Create notification service."""
        return NotificationService()

    @pytest.fixture
    def repository(self):
        """Create notification repository."""
        return NotificationRepository()

    async def test_global_subscription_matches_all_organizations(self, service, repository, user):
        """Verify global subscription (org_id=None) matches events from any organization."""
        # Create global subscription
        await repository.create_subscription(
            user=user,
            event_type=NotificationEventType.CREW_APPROVED,
            notification_method=NotificationMethod.DISCORD_DM,
            organization=None,  # Global
        )

        # Queue notification for org 1
        event_data = {"match_id": 1, "role": "Tracker"}
        log_ids = await service.queue_notification(
            user=user,
            event_type=NotificationEventType.CREW_APPROVED,
            event_data=event_data,
            organization_id=1,  # Org 1
        )

        # Should create notification
        assert len(log_ids) == 1

        # Queue notification for org 2
        log_ids = await service.queue_notification(
            user=user,
            event_type=NotificationEventType.CREW_APPROVED,
            event_data=event_data,
            organization_id=2,  # Org 2
        )

        # Should also create notification
        assert len(log_ids) == 1

    async def test_org_scoped_subscription_only_matches_that_org(self, service, repository, user):
        """Verify org-scoped subscription only matches events from that organization."""
        from models.organizations import Organization

        # Create organization
        org1 = Organization(id=1, name="Org 1", slug="org1")
        await org1.save()

        # Create org-scoped subscription
        await repository.create_subscription(
            user=user,
            event_type=NotificationEventType.CREW_APPROVED,
            notification_method=NotificationMethod.DISCORD_DM,
            organization=org1,  # Scoped to org1
        )

        # Queue notification for org 1
        event_data = {"match_id": 1, "role": "Tracker"}
        log_ids = await service.queue_notification(
            user=user,
            event_type=NotificationEventType.CREW_APPROVED,
            event_data=event_data,
            organization_id=1,  # Matching org
        )

        # Should create notification
        assert len(log_ids) == 1

        # Queue notification for org 2
        log_ids = await service.queue_notification(
            user=user,
            event_type=NotificationEventType.CREW_APPROVED,
            event_data=event_data,
            organization_id=2,  # Different org
        )

        # Should NOT create notification
        assert len(log_ids) == 0

    async def test_multiple_subscriptions_different_scopes(self, service, repository, user):
        """Verify user can have both global and org-scoped subscriptions."""
        from models.organizations import Organization

        # Create organization
        org1 = Organization(id=1, name="Org 1", slug="org1")
        await org1.save()

        # Create global subscription for CREW_APPROVED
        await repository.create_subscription(
            user=user,
            event_type=NotificationEventType.CREW_APPROVED,
            notification_method=NotificationMethod.DISCORD_DM,
            organization=None,
        )

        # Create org-scoped subscription for MATCH_SCHEDULED
        await repository.create_subscription(
            user=user,
            event_type=NotificationEventType.MATCH_SCHEDULED,
            notification_method=NotificationMethod.DISCORD_DM,
            organization=org1,
        )

        # Queue CREW_APPROVED for org 1 (should match global subscription)
        log_ids = await service.queue_notification(
            user=user,
            event_type=NotificationEventType.CREW_APPROVED,
            event_data={},
            organization_id=1,
        )
        assert len(log_ids) == 1

        # Queue MATCH_SCHEDULED for org 1 (should match org-scoped subscription)
        log_ids = await service.queue_notification(
            user=user,
            event_type=NotificationEventType.MATCH_SCHEDULED,
            event_data={},
            organization_id=1,
        )
        assert len(log_ids) == 1

        # Queue MATCH_SCHEDULED for org 2 (should NOT match - wrong org)
        log_ids = await service.queue_notification(
            user=user,
            event_type=NotificationEventType.MATCH_SCHEDULED,
            event_data={},
            organization_id=2,
        )
        assert len(log_ids) == 0
