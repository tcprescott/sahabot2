"""
Unit tests for DiscordScheduledEventRepository.

Tests the data access layer for Discord scheduled event operations.
"""

import pytest
from datetime import datetime, timezone
from application.repositories.discord_scheduled_event_repository import DiscordScheduledEventRepository
from models import DiscordScheduledEvent, Organization, Tournament, Match, User, Permission


@pytest.fixture
async def sample_org(db):
    """Create a sample organization for testing."""
    return await Organization.create(
        name="Test Organization",
        slug="test-org",
    )


@pytest.fixture
async def sample_tournament(db, sample_org):
    """Create a sample tournament for testing."""
    return await Tournament.create(
        organization=sample_org,
        name="Test Tournament",
        is_active=True,
        tracker_enabled=True,
        create_scheduled_events=True,
        scheduled_events_enabled=True,
    )


@pytest.fixture
async def sample_match(db, sample_tournament):
    """Create a sample match for testing."""
    return await Match.create(
        tournament=sample_tournament,
        scheduled_at=datetime.now(timezone.utc),
    )


@pytest.fixture
async def sample_event(db, sample_org, sample_match):
    """Create a sample Discord scheduled event for testing."""
    return await DiscordScheduledEvent.create(
        organization_id=sample_org.id,
        match_id=sample_match.id,
        scheduled_event_id=1234567890,
        event_slug="test-event",
    )


@pytest.mark.unit
@pytest.mark.asyncio
class TestDiscordScheduledEventRepository:
    """Test cases for DiscordScheduledEventRepository."""

    async def test_create(self, db, sample_org, sample_match):
        """Test creating a Discord scheduled event record."""
        repo = DiscordScheduledEventRepository()

        event = await repo.create(
            scheduled_event_id=9876543210,
            match_id=sample_match.id,
            organization_id=sample_org.id,
            event_slug="new-event",
        )

        assert event is not None
        assert event.scheduled_event_id == 9876543210
        assert event.match_id == sample_match.id
        assert event.organization_id == sample_org.id
        assert event.event_slug == "new-event"

    async def test_get_by_match(self, db, sample_org, sample_match, sample_event):
        """Test retrieving event by match ID."""
        repo = DiscordScheduledEventRepository()

        event = await repo.get_by_match(sample_org.id, sample_match.id)

        assert event is not None
        assert event.id == sample_event.id
        assert event.match_id == sample_match.id

    async def test_get_by_match_not_found(self, db, sample_org):
        """Test retrieving non-existent event returns None."""
        repo = DiscordScheduledEventRepository()

        event = await repo.get_by_match(sample_org.id, 99999)

        assert event is None

    async def test_list_for_match(self, db, sample_org, sample_match):
        """Test listing all events for a match."""
        repo = DiscordScheduledEventRepository()

        # Create multiple events for the same match
        event1 = await repo.create(
            scheduled_event_id=1111111111,
            match_id=sample_match.id,
            organization_id=sample_org.id,
        )
        event2 = await repo.create(
            scheduled_event_id=2222222222,
            match_id=sample_match.id,
            organization_id=sample_org.id,
        )

        events = await repo.list_for_match(sample_org.id, sample_match.id)

        assert len(events) == 2
        event_ids = {e.id for e in events}
        assert event1.id in event_ids
        assert event2.id in event_ids

    async def test_get_by_event_id(self, db, sample_org, sample_event):
        """Test retrieving event by Discord event ID."""
        repo = DiscordScheduledEventRepository()

        event = await repo.get_by_event_id(sample_org.id, 1234567890)

        assert event is not None
        assert event.id == sample_event.id
        assert event.scheduled_event_id == 1234567890

    async def test_list_for_tournament(self, db, sample_org, sample_tournament, sample_match, sample_event):
        """Test listing events for a tournament."""
        repo = DiscordScheduledEventRepository()

        events = await repo.list_for_tournament(sample_org.id, sample_tournament.id)

        assert len(events) >= 1
        assert any(e.id == sample_event.id for e in events)

    async def test_list_for_org(self, db, sample_org, sample_event):
        """Test listing all events for an organization."""
        repo = DiscordScheduledEventRepository()

        events = await repo.list_for_org(sample_org.id)

        assert len(events) >= 1
        assert any(e.id == sample_event.id for e in events)

    async def test_delete(self, db, sample_org, sample_match, sample_event):
        """Test deleting an event."""
        repo = DiscordScheduledEventRepository()

        result = await repo.delete(sample_org.id, sample_match.id)

        assert result is True

        # Verify deletion
        event = await repo.get_by_match(sample_org.id, sample_match.id)
        assert event is None

    async def test_delete_not_found(self, db, sample_org):
        """Test deleting non-existent event returns False."""
        repo = DiscordScheduledEventRepository()

        result = await repo.delete(sample_org.id, 99999)

        assert result is False

    async def test_delete_by_event_id(self, db, sample_org, sample_event):
        """Test deleting by Discord event ID."""
        repo = DiscordScheduledEventRepository()

        result = await repo.delete_by_event_id(sample_org.id, 1234567890)

        assert result is True

        # Verify deletion
        event = await repo.get_by_event_id(sample_org.id, 1234567890)
        assert event is None

    async def test_delete_by_id(self, db, sample_event):
        """Test deleting by database ID."""
        repo = DiscordScheduledEventRepository()

        result = await repo.delete_by_id(sample_event.id)

        assert result is True

        # Verify deletion
        event = await DiscordScheduledEvent.get_or_none(id=sample_event.id)
        assert event is None

    async def test_list_upcoming_events(self, db, sample_org, sample_tournament):
        """Test listing upcoming events."""
        repo = DiscordScheduledEventRepository()

        # Create future match with event
        future_match = await Match.create(
            tournament=sample_tournament,
            scheduled_at=datetime.now(timezone.utc),
        )
        await repo.create(
            scheduled_event_id=3333333333,
            match_id=future_match.id,
            organization_id=sample_org.id,
        )

        events = await repo.list_upcoming_events(sample_org.id, hours_future=168)

        assert len(events) >= 1

    async def test_list_orphaned_events(self, db, sample_org, sample_tournament):
        """Test listing orphaned events for finished matches."""
        repo = DiscordScheduledEventRepository()

        # Create finished match with event
        finished_match = await Match.create(
            tournament=sample_tournament,
            scheduled_at=datetime.now(timezone.utc),
            finished_at=datetime.now(timezone.utc),
        )
        await repo.create(
            scheduled_event_id=4444444444,
            match_id=finished_match.id,
            organization_id=sample_org.id,
        )

        events = await repo.list_orphaned_events(sample_org.id)

        assert len(events) >= 1
        assert any(e.match_id == finished_match.id for e in events)

    async def test_tenant_isolation(self, db, sample_match):
        """Test that events are properly isolated by organization."""
        repo = DiscordScheduledEventRepository()

        # Create two organizations
        org1 = await Organization.create(name="Org 1", slug="org-1")
        org2 = await Organization.create(name="Org 2", slug="org-2")

        # Create event in org1
        event1 = await repo.create(
            scheduled_event_id=5555555555,
            match_id=sample_match.id,
            organization_id=org1.id,
        )

        # Try to retrieve from org2
        event = await repo.get_by_match(org2.id, sample_match.id)
        assert event is None

        # Verify it exists in org1
        event = await repo.get_by_match(org1.id, sample_match.id)
        assert event is not None
        assert event.id == event1.id
