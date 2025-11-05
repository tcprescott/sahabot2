"""
Unit tests for orphaned Discord scheduled event cleanup.

Tests the cleanup logic for orphaned events (finished matches, disabled tournaments).
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timezone
from application.services.discord_scheduled_event_service import DiscordScheduledEventService
from application.repositories.discord_scheduled_event_repository import DiscordScheduledEventRepository
from models import Organization, Tournament, Match, DiscordScheduledEvent, DiscordGuild, SYSTEM_USER_ID


@pytest.fixture
async def sample_org(db):
    """Create a sample organization for testing."""
    return await Organization.create(
        name="Test Organization",
        slug="test-org",
    )


@pytest.fixture
async def sample_discord_guild(db, sample_org):
    """Create a sample Discord guild for testing."""
    return await DiscordGuild.create(
        organization=sample_org,
        guild_id=987654321098765432,
        guild_name="Test Guild",
        is_active=True,
    )


@pytest.fixture
async def sample_tournament(db, sample_org, sample_discord_guild):
    """Create a sample tournament for testing."""
    tournament = await Tournament.create(
        organization=sample_org,
        name="Test Tournament",
        is_active=True,
        tracker_enabled=True,
        create_scheduled_events=True,
        scheduled_events_enabled=True,
    )
    await tournament.discord_event_guilds.add(sample_discord_guild)
    return tournament


@pytest.mark.unit
@pytest.mark.asyncio
class TestOrphanedEventCleanup:
    """Test cases for orphaned event cleanup functionality."""

    async def test_list_orphaned_events_finished_matches(self, db, sample_org, sample_tournament):
        """Test finding events for finished matches."""
        repo = DiscordScheduledEventRepository()

        # Create finished match with event
        finished_match = await Match.create(
            tournament=sample_tournament,
            scheduled_at=datetime.now(timezone.utc),
            finished_at=datetime.now(timezone.utc),
        )
        await DiscordScheduledEvent.create(
            organization_id=sample_org.id,
            match_id=finished_match.id,
            scheduled_event_id=1111111111,
        )

        # Create active match with event (should not be returned)
        active_match = await Match.create(
            tournament=sample_tournament,
            scheduled_at=datetime.now(timezone.utc),
        )
        await DiscordScheduledEvent.create(
            organization_id=sample_org.id,
            match_id=active_match.id,
            scheduled_event_id=2222222222,
        )

        orphaned = await repo.list_orphaned_events(sample_org.id)

        assert len(orphaned) == 1
        assert orphaned[0].match_id == finished_match.id

    async def test_list_events_for_disabled_tournaments(self, db, sample_org, sample_tournament):
        """Test finding events for tournaments with events disabled."""
        repo = DiscordScheduledEventRepository()

        # Create match with event
        match = await Match.create(
            tournament=sample_tournament,
            scheduled_at=datetime.now(timezone.utc),
        )
        event = await DiscordScheduledEvent.create(
            organization_id=sample_org.id,
            match_id=match.id,
            scheduled_event_id=3333333333,
        )

        # Initially no disabled events
        disabled = await repo.list_events_for_disabled_tournaments(sample_org.id)
        assert len(disabled) == 0

        # Disable scheduled events
        sample_tournament.scheduled_events_enabled = False
        await sample_tournament.save()

        # Now should find the event
        disabled = await repo.list_events_for_disabled_tournaments(sample_org.id)
        assert len(disabled) == 1
        assert disabled[0].id == event.id

    async def test_list_events_for_create_disabled_tournaments(self, db, sample_org, sample_tournament):
        """Test finding events for tournaments with create_scheduled_events=False."""
        repo = DiscordScheduledEventRepository()

        # Create match with event
        match = await Match.create(
            tournament=sample_tournament,
            scheduled_at=datetime.now(timezone.utc),
        )
        event = await DiscordScheduledEvent.create(
            organization_id=sample_org.id,
            match_id=match.id,
            scheduled_event_id=4444444444,
        )

        # Disable create_scheduled_events
        sample_tournament.create_scheduled_events = False
        await sample_tournament.save()

        # Should find the event
        disabled = await repo.list_events_for_disabled_tournaments(sample_org.id)
        assert len(disabled) == 1
        assert disabled[0].id == event.id

    async def test_cleanup_all_orphaned_events(self, db, sample_org, sample_tournament):
        """Test comprehensive cleanup finds all types of orphaned events."""
        repo = DiscordScheduledEventRepository()

        # Create finished match with event
        finished_match = await Match.create(
            tournament=sample_tournament,
            scheduled_at=datetime.now(timezone.utc),
            finished_at=datetime.now(timezone.utc),
        )
        await DiscordScheduledEvent.create(
            organization_id=sample_org.id,
            match_id=finished_match.id,
            scheduled_event_id=5555555555,
        )

        # Disable tournament events
        sample_tournament.scheduled_events_enabled = False
        await sample_tournament.save()

        # Create match in disabled tournament
        disabled_match = await Match.create(
            tournament=sample_tournament,
            scheduled_at=datetime.now(timezone.utc),
        )
        await DiscordScheduledEvent.create(
            organization_id=sample_org.id,
            match_id=disabled_match.id,
            scheduled_event_id=6666666666,
        )

        # Get all orphaned events
        all_orphaned = await repo.cleanup_all_orphaned_events(sample_org.id)

        # Should find both events (finished and disabled)
        assert len(all_orphaned) == 2
        event_ids = {e.match_id for e in all_orphaned}
        assert finished_match.id in event_ids
        assert disabled_match.id in event_ids

    @patch('application.services.discord_scheduled_event_service.get_bot_instance')
    async def test_cleanup_orphaned_events_service(
        self, mock_get_bot, db, sample_org, sample_tournament, sample_discord_guild
    ):
        """Test service method for cleaning up orphaned events."""
        # Create finished match with event
        finished_match = await Match.create(
            tournament=sample_tournament,
            scheduled_at=datetime.now(timezone.utc),
            finished_at=datetime.now(timezone.utc),
        )
        await DiscordScheduledEvent.create(
            organization_id=sample_org.id,
            match_id=finished_match.id,
            scheduled_event_id=7777777777,
        )

        # Mock Discord bot
        mock_bot = MagicMock()
        mock_guild = MagicMock()
        mock_guild.id = sample_discord_guild.guild_id
        mock_discord_event = MagicMock()
        mock_discord_event.delete = AsyncMock()
        mock_guild.fetch_scheduled_event = AsyncMock(return_value=mock_discord_event)
        mock_bot.get_guild.return_value = mock_guild
        mock_get_bot.return_value = mock_bot

        service = DiscordScheduledEventService()
        stats = await service.cleanup_orphaned_events(
            user_id=SYSTEM_USER_ID,
            organization_id=sample_org.id,
        )

        assert stats['deleted'] >= 1
        assert stats['errors'] == 0

        # Verify database record deleted
        events = await DiscordScheduledEvent.filter(match_id=finished_match.id).all()
        assert len(events) == 0

    async def test_tenant_isolation_orphaned_cleanup(self, db, sample_tournament):
        """Test that orphaned cleanup respects organization boundaries."""
        repo = DiscordScheduledEventRepository()

        # Create two organizations
        org1 = await Organization.create(name="Org 1", slug="org-1")
        org2 = await Organization.create(name="Org 2", slug="org-2")

        # Create finished match in org1
        finished_match = await Match.create(
            tournament=sample_tournament,
            scheduled_at=datetime.now(timezone.utc),
            finished_at=datetime.now(timezone.utc),
        )
        await DiscordScheduledEvent.create(
            organization_id=org1.id,
            match_id=finished_match.id,
            scheduled_event_id=8888888888,
        )

        # Cleanup in org2 should find nothing
        orphaned_org2 = await repo.list_orphaned_events(org2.id)
        assert len(orphaned_org2) == 0

        # Cleanup in org1 should find the event
        orphaned_org1 = await repo.list_orphaned_events(org1.id)
        assert len(orphaned_org1) == 1

    async def test_no_duplicate_events_in_cleanup(self, db, sample_org, sample_tournament):
        """Test that events are not duplicated when matching multiple criteria."""
        repo = DiscordScheduledEventRepository()

        # Create match that is both finished AND in disabled tournament
        sample_tournament.scheduled_events_enabled = False
        await sample_tournament.save()

        finished_match = await Match.create(
            tournament=sample_tournament,
            scheduled_at=datetime.now(timezone.utc),
            finished_at=datetime.now(timezone.utc),
        )
        event = await DiscordScheduledEvent.create(
            organization_id=sample_org.id,
            match_id=finished_match.id,
            scheduled_event_id=9999999999,
        )

        # Get all orphaned events
        all_orphaned = await repo.cleanup_all_orphaned_events(sample_org.id)

        # Should only appear once, not twice
        event_ids = [e.id for e in all_orphaned]
        assert event_ids.count(event.id) == 1
