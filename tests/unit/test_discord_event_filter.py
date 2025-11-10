"""Tests for Discord event filter functionality."""

import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
import discord

from models import Tournament, Match, DiscordEventFilter, StreamChannel, User
from application.services.discord.discord_scheduled_event_service import (
    DiscordScheduledEventService,
)


@pytest.fixture
async def sample_user(db):
    """Create a sample user for testing."""
    user = await User.create(
        discord_id=12345,
        discord_username="test_user",
        discord_discriminator="0001",
    )
    return user


@pytest.fixture
async def sample_tournament(db):
    """Create a sample tournament for testing."""
    from models import Organization

    org = await Organization.create(name="Test Org", slug="test-org")
    tournament = await Tournament.create(
        organization_id=org.id,
        name="Test Tournament",
        create_scheduled_events=True,
        scheduled_events_enabled=True,
        discord_event_filter=DiscordEventFilter.ALL,
    )
    return tournament


@pytest.fixture
async def sample_stream_channel(db, sample_tournament):
    """Create a sample stream channel."""
    stream = await StreamChannel.create(
        organization_id=sample_tournament.organization_id,
        name="Main Stream",
        stream_url="https://twitch.tv/test_channel",
    )
    return stream


@pytest.fixture
async def sample_match_with_stream(db, sample_tournament, sample_stream_channel):
    """Create a match with a stream assigned."""
    match = await Match.create(
        tournament_id=sample_tournament.id,
        scheduled_at=datetime.now(timezone.utc) + timedelta(hours=1),
        stream_channel_id=sample_stream_channel.id,
        title="Finals",
    )
    await match.fetch_related("tournament", "stream_channel")
    return match


@pytest.fixture
async def sample_match_no_stream(db, sample_tournament):
    """Create a match without a stream assigned."""
    match = await Match.create(
        tournament_id=sample_tournament.id,
        scheduled_at=datetime.now(timezone.utc) + timedelta(hours=2),
        title="Qualifier",
    )
    await match.fetch_related("tournament", "stream_channel")
    return match


class TestDiscordEventFilter:
    """Test cases for Discord event filtering."""

    def setup_method(self):
        """Set up test fixtures."""
        self.service = DiscordScheduledEventService()

    @pytest.mark.asyncio
    async def test_filter_all_includes_all_matches(
        self, db, sample_tournament, sample_match_with_stream, sample_match_no_stream
    ):
        """Test that ALL filter includes matches with and without streams."""
        # Arrange
        sample_tournament.discord_event_filter = DiscordEventFilter.ALL
        await sample_tournament.save()

        # Act & Assert - Both should pass the filter
        assert (
            self.service._should_create_event_for_match(
                sample_match_with_stream, sample_tournament
            )
            is True
        )
        assert (
            self.service._should_create_event_for_match(
                sample_match_no_stream, sample_tournament
            )
            is True
        )

    @pytest.mark.asyncio
    async def test_filter_stream_only_includes_streamed_matches(
        self, db, sample_tournament, sample_match_with_stream, sample_match_no_stream
    ):
        """Test that STREAM_ONLY filter only includes matches with streams."""
        # Arrange
        sample_tournament.discord_event_filter = DiscordEventFilter.STREAM_ONLY
        await sample_tournament.save()

        # Act & Assert
        assert (
            self.service._should_create_event_for_match(
                sample_match_with_stream, sample_tournament
            )
            is True
        )
        assert (
            self.service._should_create_event_for_match(
                sample_match_no_stream, sample_tournament
            )
            is False
        )

    @pytest.mark.asyncio
    async def test_filter_none_excludes_all_matches(
        self, db, sample_tournament, sample_match_with_stream, sample_match_no_stream
    ):
        """Test that NONE filter excludes all matches."""
        # Arrange
        sample_tournament.discord_event_filter = DiscordEventFilter.NONE
        await sample_tournament.save()

        # Act & Assert
        assert (
            self.service._should_create_event_for_match(
                sample_match_with_stream, sample_tournament
            )
            is False
        )
        assert (
            self.service._should_create_event_for_match(
                sample_match_no_stream, sample_tournament
            )
            is False
        )

    @pytest.mark.asyncio
    async def test_create_event_respects_filter(
        self, db, sample_tournament, sample_match_no_stream
    ):
        """Test that create_event_for_match respects the filter setting."""
        # Arrange
        sample_tournament.discord_event_filter = DiscordEventFilter.STREAM_ONLY
        await sample_tournament.save()

        # Mock Discord bot
        mock_bot = MagicMock()
        with patch(
            "application.services.discord.discord_scheduled_event_service.get_bot_instance",
            return_value=mock_bot,
        ):
            # Act
            result = await self.service.create_event_for_match(
                user_id=1,
                organization_id=sample_tournament.organization_id,
                match_id=sample_match_no_stream.id,
            )

            # Assert - Should return None (filtered out)
            assert result is None

    @pytest.mark.asyncio
    async def test_create_event_with_stream_passes_filter(
        self, db, sample_tournament, sample_match_with_stream, sample_user
    ):
        """Test that matches with streams pass the STREAM_ONLY filter."""
        # Arrange
        sample_tournament.discord_event_filter = DiscordEventFilter.STREAM_ONLY
        await sample_tournament.save()

        # Mock Discord components
        mock_bot = MagicMock()
        mock_guild = MagicMock()
        mock_guild.id = 123456789
        mock_guild.me = MagicMock()
        mock_guild.me.guild_permissions.manage_events = True
        mock_bot.get_guild.return_value = mock_guild

        # Mock Discord event creation
        mock_event = MagicMock()
        mock_event.id = 987654321
        mock_guild.create_scheduled_event = AsyncMock(return_value=mock_event)

        # Mock DiscordGuild
        from models import DiscordGuild

        discord_guild = await DiscordGuild.create(
            organization_id=sample_tournament.organization_id,
            guild_id=123456789,
            guild_name="Test Guild",
            is_active=True,
            linked_by_id=sample_user.id,
        )
        await sample_tournament.discord_event_guilds.add(discord_guild)

        with patch(
            "application.services.discord.discord_scheduled_event_service.get_bot_instance",
            return_value=mock_bot,
        ):
            # Act
            result = await self.service.create_event_for_match(
                user_id=1,
                organization_id=sample_tournament.organization_id,
                match_id=sample_match_with_stream.id,
            )

            # Assert - Should create event (not filtered out)
            assert result is not None
            mock_guild.create_scheduled_event.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_deletes_events_when_filter_changes(
        self, db, sample_tournament, sample_match_no_stream
    ):
        """Test that update_event_for_match deletes events when match no longer passes filter."""
        # Arrange - Create event first with ALL filter
        sample_tournament.discord_event_filter = DiscordEventFilter.ALL
        await sample_tournament.save()

        # Create a mock event in the database
        from models import DiscordScheduledEvent

        event = await DiscordScheduledEvent.create(
            scheduled_event_id=111111,
            match_id=sample_match_no_stream.id,
            organization_id=sample_tournament.organization_id,
        )

        # Change filter to STREAM_ONLY (match has no stream, so should be deleted)
        sample_tournament.discord_event_filter = DiscordEventFilter.STREAM_ONLY
        await sample_tournament.save()

        # Mock Discord bot
        mock_bot = MagicMock()
        with patch(
            "application.services.discord.discord_scheduled_event_service.get_bot_instance",
            return_value=mock_bot,
        ):
            # Act
            result = await self.service.update_event_for_match(
                user_id=1,
                organization_id=sample_tournament.organization_id,
                match_id=sample_match_no_stream.id,
            )

            # Assert - Should return False (event deleted due to filter)
            assert result is False

            # Verify event was deleted from database
            deleted_event = await DiscordScheduledEvent.get_or_none(id=event.id)
            assert deleted_event is None

    @pytest.mark.asyncio
    async def test_sync_respects_filter(
        self,
        db,
        sample_tournament,
        sample_match_with_stream,
        sample_match_no_stream,
        sample_user,
    ):
        """Test that sync_tournament_events respects the filter setting."""
        # Arrange
        sample_tournament.discord_event_filter = DiscordEventFilter.STREAM_ONLY
        await sample_tournament.save()

        # Mock Discord components (minimal setup since we're just testing filter logic)
        mock_bot = MagicMock()
        mock_guild = MagicMock()
        mock_guild.id = 123456789
        mock_guild.me = MagicMock()
        mock_guild.me.guild_permissions.manage_events = True
        mock_bot.get_guild.return_value = mock_guild

        mock_event = MagicMock()
        mock_event.id = 987654321
        mock_guild.create_scheduled_event = AsyncMock(return_value=mock_event)

        from models import DiscordGuild

        discord_guild = await DiscordGuild.create(
            organization_id=sample_tournament.organization_id,
            guild_id=123456789,
            guild_name="Test Guild",
            is_active=True,
            linked_by_id=sample_user.id,
        )
        await sample_tournament.discord_event_guilds.add(discord_guild)

        with patch(
            "application.services.discord.discord_scheduled_event_service.get_bot_instance",
            return_value=mock_bot,
        ):
            # Act
            stats = await self.service.sync_tournament_events(
                user_id=1,
                organization_id=sample_tournament.organization_id,
                tournament_id=sample_tournament.id,
            )

            # Assert - Only match with stream should create event
            # (1 created for match_with_stream, 0 for match_no_stream which is filtered out)
            assert stats["created"] == 1
            assert stats["errors"] == 0
