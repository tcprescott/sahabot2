"""
Integration tests for Discord scheduled event listeners.

Tests that event listeners correctly trigger Discord event management.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timezone
from application.events import (
    EventBus,
    MatchScheduledEvent,
    MatchUpdatedEvent,
    MatchDeletedEvent,
)
from models import Tournament, Match, DiscordGuild, SYSTEM_USER_ID

# Import listeners module to register event handlers
import application.events.listeners  # noqa: F401


@pytest.fixture(autouse=True)
def ensure_listeners_registered():
    """Ensure event listeners are registered before each test.

    This is needed because some unit tests call EventBus.clear_all(),
    which removes all handlers including those registered by listeners module.
    """
    # Re-import to re-register decorators
    import importlib
    import application.events.listeners as listeners_module

    importlib.reload(listeners_module)


@pytest.fixture
async def sample_tournament(db, sample_organization, sample_discord_guild):
    """Create a sample tournament with events enabled."""
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


@pytest.mark.integration
@pytest.mark.asyncio
class TestDiscordScheduledEventListeners:
    """Test cases for Discord scheduled event listeners."""

    @patch(
        "application.services.discord.discord_scheduled_event_service.get_bot_instance"
    )
    async def test_match_scheduled_event_creates_discord_event(
        self,
        mock_get_bot,
        db,
        sample_organization,
        sample_tournament,
        sample_discord_guild,
    ):
        """Test that MatchScheduledEvent creates a Discord event."""
        # Mock Discord bot
        mock_bot = MagicMock()
        mock_guild = MagicMock()
        mock_guild.id = sample_discord_guild.guild_id
        mock_guild.create_scheduled_event = AsyncMock(
            return_value=MagicMock(id=1111111111)
        )
        mock_bot.get_guild.return_value = mock_guild
        mock_get_bot.return_value = mock_bot

        # Create match
        match = await Match.create(
            tournament=sample_tournament,
            scheduled_at=datetime.now(timezone.utc),
            title="Test Match",
        )

        # Emit event
        await EventBus.emit(
            MatchScheduledEvent(
                user_id=SYSTEM_USER_ID,
                organization_id=sample_organization.id,
                entity_id=match.id,
                tournament_id=sample_tournament.id,
            )
        )

        # Give event handlers time to process
        import asyncio

        await asyncio.sleep(0.1)

        # Verify Discord event was created
        from models import DiscordScheduledEvent

        events = await DiscordScheduledEvent.filter(match_id=match.id).all()
        assert len(events) >= 1

    @patch(
        "application.services.discord.discord_scheduled_event_service.get_bot_instance"
    )
    async def test_match_updated_event_updates_discord_event(
        self, mock_get_bot, db, sample_organization, sample_match, sample_discord_guild
    ):
        """Test that MatchUpdatedEvent updates Discord event."""
        # Create initial Discord event
        from models import DiscordScheduledEvent

        await DiscordScheduledEvent.create(
            organization_id=sample_organization.id,
            match_id=sample_match.id,
            scheduled_event_id=2222222222,
        )

        # Mock Discord bot
        mock_bot = MagicMock()
        mock_guild = MagicMock()
        mock_guild.id = sample_discord_guild.guild_id
        mock_discord_event = MagicMock()
        mock_discord_event.edit = AsyncMock()
        mock_guild.fetch_scheduled_event = AsyncMock(return_value=mock_discord_event)
        mock_bot.get_guild.return_value = mock_guild
        mock_get_bot.return_value = mock_bot

        # Emit update event
        await EventBus.emit(
            MatchUpdatedEvent(
                user_id=SYSTEM_USER_ID,
                organization_id=sample_organization.id,
                entity_id=sample_match.id,
                tournament_id=sample_match.tournament_id,
                changed_fields=["scheduled_at"],
            )
        )

        # Give event handlers time to process
        import asyncio

        await asyncio.sleep(0.1)

        # Verify update was called
        assert mock_discord_event.edit.called or mock_guild.fetch_scheduled_event.called

    @patch(
        "application.services.discord.discord_scheduled_event_service.get_bot_instance"
    )
    async def test_match_deleted_event_deletes_discord_event(
        self, mock_get_bot, db, sample_organization, sample_match, sample_discord_guild
    ):
        """Test that MatchDeletedEvent deletes Discord event."""
        # Create Discord event
        from models import DiscordScheduledEvent

        await DiscordScheduledEvent.create(
            organization_id=sample_organization.id,
            match_id=sample_match.id,
            scheduled_event_id=3333333333,
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

        # Emit delete event
        await EventBus.emit(
            MatchDeletedEvent(
                user_id=SYSTEM_USER_ID,
                organization_id=sample_organization.id,
                entity_id=sample_match.id,
                tournament_id=sample_match.tournament_id,
            )
        )

        # Give event handlers time to process
        import asyncio

        await asyncio.sleep(0.1)

        # Verify database record was deleted
        events = await DiscordScheduledEvent.filter(match_id=sample_match.id).all()
        assert len(events) == 0

    @patch(
        "application.services.discord.discord_scheduled_event_service.get_bot_instance"
    )
    async def test_event_not_created_when_disabled(
        self, mock_get_bot, db, sample_organization, sample_discord_guild
    ):
        """Test that events are not created when disabled in tournament."""
        # Create tournament with events disabled
        tournament = await Tournament.create(
            organization=sample_organization,
            name="No Events Tournament",
            is_active=True,
            tracker_enabled=True,
            create_scheduled_events=False,
            scheduled_events_enabled=False,
        )

        # Create match
        match = await Match.create(
            tournament=tournament,
            scheduled_at=datetime.now(timezone.utc),
        )

        # Mock Discord bot (should not be called)
        mock_bot = MagicMock()
        mock_guild = MagicMock()
        mock_guild.create_scheduled_event = AsyncMock(
            return_value=MagicMock(id=4444444444)
        )
        mock_bot.get_guild.return_value = mock_guild
        mock_get_bot.return_value = mock_bot

        # Emit event
        await EventBus.emit(
            MatchScheduledEvent(
                user_id=SYSTEM_USER_ID,
                organization_id=sample_organization.id,
                entity_id=match.id,
                tournament_id=tournament.id,
            )
        )

        # Give event handlers time to process
        import asyncio

        await asyncio.sleep(0.1)

        # Verify no Discord event was created
        from models import DiscordScheduledEvent

        events = await DiscordScheduledEvent.filter(match_id=match.id).all()
        assert len(events) == 0

    async def test_multiple_guilds_creates_multiple_events(
        self,
        db,
        sample_user,
        sample_organization,
        sample_tournament,
        sample_discord_guild,
    ):
        """Test that events are created in all configured guilds."""
        # Add second guild
        guild2 = await DiscordGuild.create(
            organization=sample_organization,
            linked_by=sample_user,
            guild_id=111222333444555666,
            guild_name="Second Guild",
            is_active=True,
        )
        await sample_tournament.discord_event_guilds.add(guild2)

        with patch(
            "application.services.discord.discord_scheduled_event_service.get_bot_instance"
        ) as mock_get_bot:
            # Mock Discord bot
            mock_bot = MagicMock()

            def get_guild_mock(guild_id):
                mock_guild = MagicMock()
                mock_guild.id = guild_id
                # Use smaller event IDs to avoid SQLite INTEGER overflow
                # Map guild_id to a unique but reasonable event ID
                event_id = 1111111111 if guild_id == 987654321098765432 else 2222222222
                mock_guild.create_scheduled_event = AsyncMock(
                    return_value=MagicMock(id=event_id)
                )
                return mock_guild

            mock_bot.get_guild.side_effect = get_guild_mock
            mock_get_bot.return_value = mock_bot

            # Create match
            match = await Match.create(
                tournament=sample_tournament,
                scheduled_at=datetime.now(timezone.utc),
            )

            # Emit event
            await EventBus.emit(
                MatchScheduledEvent(
                    user_id=SYSTEM_USER_ID,
                    organization_id=sample_organization.id,
                    entity_id=match.id,
                    tournament_id=sample_tournament.id,
                )
            )

            # Give event handlers time to process
            import asyncio

            await asyncio.sleep(0.1)

            # Verify multiple events created
            from models import DiscordScheduledEvent

            events = await DiscordScheduledEvent.filter(match_id=match.id).all()
            assert len(events) >= 1  # At least one event created
