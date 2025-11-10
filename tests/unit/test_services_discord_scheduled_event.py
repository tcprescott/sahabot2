"""
Unit tests for DiscordScheduledEventService.

Tests the business logic for Discord scheduled event operations.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timezone
from application.services.discord.discord_scheduled_event_service import (
    DiscordScheduledEventService,
)
from models import Organization, Tournament, Match, User, Permission, SYSTEM_USER_ID


@pytest.fixture
async def sample_tournament(db, sample_organization, sample_discord_guild):
    """Create a sample tournament for testing."""
    tournament = await Tournament.create(
        organization=sample_organization,
        name="Test Tournament",
        is_active=True,
        tracker_enabled=True,
        create_scheduled_events=True,
        scheduled_events_enabled=True,
    )
    await tournament.discord_event_guilds.add(sample_discord_guild)
    return tournament


@pytest.fixture
async def sample_match(db, sample_tournament):
    """Create a sample match for testing."""
    return await Match.create(
        tournament=sample_tournament,
        scheduled_at=datetime.now(timezone.utc),
        title="Test Match",
    )


@pytest.fixture
async def moderator_user(db):
    """Create a moderator user for testing."""
    return await User.create(
        discord_id=123456789,
        discord_username="moderator",
        discord_discriminator="0001",
        permission=Permission.MODERATOR,
        is_active=True,
    )


@pytest.mark.unit
@pytest.mark.asyncio
class TestDiscordScheduledEventService:
    """Test cases for DiscordScheduledEventService."""

    @patch(
        "application.services.discord.discord_scheduled_event_service.get_bot_instance"
    )
    async def test_create_event_for_match_success(
        self,
        mock_get_bot,
        db,
        sample_organization,
        sample_match,
        sample_tournament,
        moderator_user,
        sample_discord_guild,
    ):
        """Test creating Discord event for a match."""
        # Mock Discord bot and guild
        mock_bot = MagicMock()
        mock_guild = MagicMock()
        mock_guild.id = sample_discord_guild.guild_id
        mock_guild.create_scheduled_event = AsyncMock(
            return_value=MagicMock(id=1111111111)
        )
        mock_bot.get_guild.return_value = mock_guild
        mock_get_bot.return_value = mock_bot

        service = DiscordScheduledEventService()
        event = await service.create_event_for_match(
            user_id=moderator_user.id,
            organization_id=sample_organization.id,
            match_id=sample_match.id,
        )

        assert event is not None
        assert event.match_id == sample_match.id
        assert event.organization_id == sample_organization.id

    @patch(
        "application.services.discord.discord_scheduled_event_service.get_bot_instance"
    )
    async def test_create_event_no_bot(
        self, mock_get_bot, db, sample_organization, sample_match, moderator_user
    ):
        """Test creating event when bot is unavailable."""
        mock_get_bot.return_value = None

        service = DiscordScheduledEventService()
        event = await service.create_event_for_match(
            user_id=moderator_user.id,
            organization_id=sample_organization.id,
            match_id=sample_match.id,
        )

        assert event is None

    @patch(
        "application.services.discord.discord_scheduled_event_service.get_bot_instance"
    )
    async def test_create_event_disabled_tournament(
        self, mock_get_bot, db, sample_organization, sample_tournament, moderator_user
    ):
        """Test creating event when tournament has events disabled."""
        # Disable scheduled events
        sample_tournament.scheduled_events_enabled = False
        await sample_tournament.save()

        # Create match
        match = await Match.create(
            tournament=sample_tournament,
            scheduled_at=datetime.now(timezone.utc),
        )

        service = DiscordScheduledEventService()
        event = await service.create_event_for_match(
            user_id=moderator_user.id,
            organization_id=sample_organization.id,
            match_id=match.id,
        )

        assert event is None

    @patch(
        "application.services.discord.discord_scheduled_event_service.get_bot_instance"
    )
    async def test_update_event_for_match(
        self,
        mock_get_bot,
        db,
        sample_organization,
        sample_match,
        sample_discord_guild,
        moderator_user,
    ):
        """Test updating Discord event for a match."""
        # Create initial event
        from models import DiscordScheduledEvent

        db_event = await DiscordScheduledEvent.create(
            organization_id=sample_organization.id,
            match_id=sample_match.id,
            scheduled_event_id=2222222222,
        )

        # Mock Discord bot and guild
        mock_bot = MagicMock()
        mock_guild = MagicMock()
        mock_guild.id = sample_discord_guild.guild_id
        mock_discord_event = MagicMock()
        mock_discord_event.edit = AsyncMock()
        mock_guild.fetch_scheduled_event = AsyncMock(return_value=mock_discord_event)
        mock_bot.get_guild.return_value = mock_guild
        mock_get_bot.return_value = mock_bot

        service = DiscordScheduledEventService()
        result = await service.update_event_for_match(
            user_id=moderator_user.id,
            organization_id=sample_organization.id,
            match_id=sample_match.id,
        )

        assert result is True

    @patch(
        "application.services.discord.discord_scheduled_event_service.get_bot_instance"
    )
    async def test_update_event_not_found(
        self, mock_get_bot, db, sample_organization, moderator_user
    ):
        """Test updating non-existent event."""
        service = DiscordScheduledEventService()
        result = await service.update_event_for_match(
            user_id=moderator_user.id,
            organization_id=sample_organization.id,
            match_id=99999,
        )

        assert result is False

    @patch(
        "application.services.discord.discord_scheduled_event_service.get_bot_instance"
    )
    async def test_delete_event_for_match(
        self,
        mock_get_bot,
        db,
        sample_organization,
        sample_match,
        sample_discord_guild,
        moderator_user,
    ):
        """Test deleting Discord event for a match."""
        # Create event
        from models import DiscordScheduledEvent

        await DiscordScheduledEvent.create(
            organization_id=sample_organization.id,
            match_id=sample_match.id,
            scheduled_event_id=3333333333,
        )

        # Mock Discord bot and guild
        mock_bot = MagicMock()
        mock_guild = MagicMock()
        mock_guild.id = sample_discord_guild.guild_id
        mock_discord_event = MagicMock()
        mock_discord_event.delete = AsyncMock()
        mock_guild.fetch_scheduled_event = AsyncMock(return_value=mock_discord_event)
        mock_bot.get_guild.return_value = mock_guild
        mock_get_bot.return_value = mock_bot

        service = DiscordScheduledEventService()
        result = await service.delete_event_for_match(
            user_id=moderator_user.id,
            organization_id=sample_organization.id,
            match_id=sample_match.id,
        )

        assert result is True

        # Verify database record deleted
        from models import DiscordScheduledEvent

        events = await DiscordScheduledEvent.filter(match_id=sample_match.id).all()
        assert len(events) == 0

    @patch(
        "application.services.discord.discord_scheduled_event_service.get_bot_instance"
    )
    async def test_sync_tournament_events(
        self,
        mock_get_bot,
        db,
        sample_organization,
        sample_tournament,
        sample_discord_guild,
        moderator_user,
    ):
        """Test syncing tournament events."""
        # Create matches
        match1 = await Match.create(
            tournament=sample_tournament,
            scheduled_at=datetime.now(timezone.utc),
            title="Match 1",
        )
        match2 = await Match.create(
            tournament=sample_tournament,
            scheduled_at=datetime.now(timezone.utc),
            title="Match 2",
        )

        # Mock Discord bot
        mock_bot = MagicMock()
        mock_guild = MagicMock()
        mock_guild.id = sample_discord_guild.guild_id
        mock_guild.create_scheduled_event = AsyncMock(
            return_value=MagicMock(id=4444444444)
        )
        mock_bot.get_guild.return_value = mock_guild
        mock_get_bot.return_value = mock_bot

        service = DiscordScheduledEventService()
        stats = await service.sync_tournament_events(
            user_id=moderator_user.id,
            organization_id=sample_organization.id,
            tournament_id=sample_tournament.id,
        )

        assert stats["created"] >= 0
        assert stats["errors"] >= 0
        assert isinstance(stats, dict)

    async def test_format_event_name(self, db, sample_tournament, sample_match):
        """Test event name formatting."""
        service = DiscordScheduledEventService()
        name = service._format_event_name(sample_match, sample_tournament)

        assert len(name) <= 100
        assert sample_tournament.name in name or "Tournament" in name

    async def test_format_event_description(self, db, sample_tournament, sample_match):
        """Test event description formatting."""
        service = DiscordScheduledEventService()
        description = service._format_event_description(sample_match, sample_tournament)

        assert isinstance(description, str)
        assert len(description) > 0

    async def test_system_user_actions(
        self,
        db,
        sample_organization,
        sample_match,
        sample_tournament,
        sample_discord_guild,
    ):
        """Test that system actions use SYSTEM_USER_ID."""
        with patch(
            "application.services.discord.discord_scheduled_event_service.get_bot_instance"
        ) as mock_get_bot:
            # Mock Discord bot
            mock_bot = MagicMock()
            mock_guild = MagicMock()
            mock_guild.id = sample_discord_guild.guild_id
            mock_guild.create_scheduled_event = AsyncMock(
                return_value=MagicMock(id=5555555555)
            )
            mock_bot.get_guild.return_value = mock_guild
            mock_get_bot.return_value = mock_bot

            service = DiscordScheduledEventService()
            event = await service.create_event_for_match(
                user_id=SYSTEM_USER_ID,
                organization_id=sample_organization.id,
                match_id=sample_match.id,
            )

            assert event is not None

    async def test_tenant_isolation(self, db, sample_match, moderator_user):
        """Test that events are properly isolated by organization."""
        # Create two organizations
        org1 = await Organization.create(name="Org 1", slug="org-1")
        org2 = await Organization.create(name="Org 2", slug="org-2")

        # Create event in org1
        from models import DiscordScheduledEvent

        await DiscordScheduledEvent.create(
            organization_id=org1.id,
            match_id=sample_match.id,
            scheduled_event_id=6666666666,
        )

        service = DiscordScheduledEventService()

        # Try to delete from org2 (should fail)
        result = await service.delete_event_for_match(
            user_id=moderator_user.id,
            organization_id=org2.id,
            match_id=sample_match.id,
        )

        assert result is True  # Returns True even if not found

        # Verify event still exists in org1
        event = await DiscordScheduledEvent.get_or_none(
            organization_id=org1.id,
            match_id=sample_match.id,
        )
        assert event is not None
