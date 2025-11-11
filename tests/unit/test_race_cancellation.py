"""
Tests for race cancellation handling.

Verifies that:
1. Race status events include match_id when handler is a match handler
2. Race cancellation events unlink room from match
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from application.events.listeners.racetime_listeners import (
    advance_match_on_race_status_changed,
)
from application.events.types import RacetimeRaceStatusChangedEvent
from models import SYSTEM_USER_ID


class TestRaceCancellation:
    """Test race cancellation handling."""

    @pytest.mark.asyncio
    async def test_race_cancelled_unlinks_room_from_match(self):
        """Test that race cancellation unlinks the room from the match."""
        # Create a race status changed event with cancelled status
        event = RacetimeRaceStatusChangedEvent(
            user_id=SYSTEM_USER_ID,
            entity_id="alttpr/test-room-1234",
            category="alttpr",
            room_slug="alttpr/test-room-1234",
            room_name="test-room-1234",
            old_status="in_progress",
            new_status="cancelled",
            match_id=42,
            tournament_id=1,
            entrant_count=2,
        )

        # Mock Match to return a match
        mock_match = MagicMock()
        mock_match.id = 42
        mock_match.started_at = None
        mock_match.finished_at = None

        # Mock RacetimeRoom to return a room
        mock_room = MagicMock()
        mock_room.slug = "alttpr/test-room-1234"
        mock_room.match_id = 42
        mock_room.delete = AsyncMock()

        with patch("application.events.listeners.racetime_listeners.Match") as mock_match_model:
            mock_filter = MagicMock()
            mock_filter.first = AsyncMock(return_value=mock_match)
            mock_match_model.filter = MagicMock(return_value=mock_filter)

            with patch(
                "application.events.listeners.racetime_listeners.RacetimeRoom"
            ) as mock_room_model:
                mock_room_filter = MagicMock()
                mock_room_filter.first = AsyncMock(return_value=mock_room)
                mock_room_model.filter = MagicMock(return_value=mock_room_filter)

                # Call the event listener
                await advance_match_on_race_status_changed(event)

                # Verify room was deleted (unlinked)
                mock_room.delete.assert_called_once()
                # Verify correct room was queried
                mock_room_model.filter.assert_called_once_with(
                    slug="alttpr/test-room-1234", match_id=42
                )

    @pytest.mark.asyncio
    async def test_race_cancelled_handles_missing_room_gracefully(self):
        """Test that cancellation handles missing room gracefully."""
        event = RacetimeRaceStatusChangedEvent(
            user_id=SYSTEM_USER_ID,
            entity_id="alttpr/test-room-1234",
            category="alttpr",
            room_slug="alttpr/test-room-1234",
            room_name="test-room-1234",
            old_status="in_progress",
            new_status="cancelled",
            match_id=42,
            tournament_id=1,
            entrant_count=2,
        )

        # Mock Match to return a match
        mock_match = MagicMock()
        mock_match.id = 42

        with patch("application.events.listeners.racetime_listeners.Match") as mock_match_model:
            mock_filter = MagicMock()
            mock_filter.first = AsyncMock(return_value=mock_match)
            mock_match_model.filter = MagicMock(return_value=mock_filter)

            with patch(
                "application.events.listeners.racetime_listeners.RacetimeRoom"
            ) as mock_room_model:
                # Return None (no room found)
                mock_room_filter = MagicMock()
                mock_room_filter.first = AsyncMock(return_value=None)
                mock_room_model.filter = MagicMock(return_value=mock_room_filter)

                # Call should not raise an exception
                await advance_match_on_race_status_changed(event)

                # Verify filter was called
                mock_room_model.filter.assert_called_once()

    @pytest.mark.asyncio
    async def test_race_in_progress_advances_match_to_started(self):
        """Test that race in_progress advances match to started status."""
        event = RacetimeRaceStatusChangedEvent(
            user_id=SYSTEM_USER_ID,
            entity_id="alttpr/test-room-1234",
            category="alttpr",
            room_slug="alttpr/test-room-1234",
            room_name="test-room-1234",
            old_status="pending",
            new_status="in_progress",
            match_id=42,
            tournament_id=1,
            entrant_count=2,
        )

        # Mock Match to return a match
        mock_match = MagicMock()
        mock_match.id = 42
        mock_match.started_at = None
        mock_match.finished_at = None
        mock_match.save = AsyncMock()

        with patch("application.events.listeners.racetime_listeners.Match") as mock_match_model:
            mock_filter = MagicMock()
            mock_filter.first = AsyncMock(return_value=mock_match)
            mock_match_model.filter = MagicMock(return_value=mock_filter)

            # Call the event listener
            await advance_match_on_race_status_changed(event)

            # Verify match was saved
            mock_match.save.assert_called_once()
            # Verify started_at was set
            assert mock_match.started_at is not None

    @pytest.mark.asyncio
    async def test_race_finished_advances_match_to_finished(self):
        """Test that race finished advances match to finished status."""
        event = RacetimeRaceStatusChangedEvent(
            user_id=SYSTEM_USER_ID,
            entity_id="alttpr/test-room-1234",
            category="alttpr",
            room_slug="alttpr/test-room-1234",
            room_name="test-room-1234",
            old_status="in_progress",
            new_status="finished",
            match_id=42,
            tournament_id=1,
            entrant_count=2,
        )

        # Mock Match to return a match
        mock_match = MagicMock()
        mock_match.id = 42
        mock_match.started_at = None
        mock_match.finished_at = None
        mock_match.save = AsyncMock()

        with patch("application.events.listeners.racetime_listeners.Match") as mock_match_model:
            mock_filter = MagicMock()
            mock_filter.first = AsyncMock(return_value=mock_match)
            mock_match_model.filter = MagicMock(return_value=mock_filter)

            with patch("application.events.listeners.racetime_listeners.EventBus") as mock_bus:
                # Mock emit to avoid actual event emission
                mock_bus.emit = AsyncMock()

                # Call the event listener
                await advance_match_on_race_status_changed(event)

                # Verify match was saved
                mock_match.save.assert_called_once()
                # Verify finished_at was set
                assert mock_match.finished_at is not None
                # Verify MatchFinishedEvent was emitted
                mock_bus.emit.assert_called_once()
