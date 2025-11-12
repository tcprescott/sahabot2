"""
Test automatic acceptance of join requests for match players.

Verifies that when a player requests to join an invitational RaceTime race room,
if they are listed as a player on the match, their request is automatically accepted.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from models import User, Permission
from models.match_schedule import Match, MatchPlayers
from racetime.handlers.base_handler import SahaRaceHandler


@pytest.mark.asyncio
async def test_auto_accept_join_request_for_match_player():
    """Test that join requests are auto-accepted for players on the match."""
    # Track accept_request calls
    accepted_users = []

    # Create mock handler
    handler = SahaRaceHandler(
        bot_instance=MagicMock(),
        logger=AsyncMock(),
        conn=AsyncMock(),
        state={},
    )

    # Mock accept_request method
    async def track_accept(racetime_id: str):
        """Track which users were accepted."""
        accepted_users.append(racetime_id)

    handler.accept_request = AsyncMock(side_effect=track_accept)

    # Set up handler data
    handler.data = {
        "name": "alttpr/test-room-1234",
        "category": {"slug": "alttpr"},
        "status": {"value": "open"},
    }

    # Mock RacetimeRoomService to return that user is a match player
    with patch(
        "application.services.racetime.racetime_room_service.RacetimeRoomService"
    ) as MockService:
        mock_service_instance = AsyncMock()
        mock_service_instance.is_player_on_match = AsyncMock(return_value=(True, 1))
        MockService.return_value = mock_service_instance

        # Test the join request handler
        await handler._handle_join_request(
            racetime_user_id="abc123",
            racetime_user_name="Player1RT",
            room_slug="alttpr/test-room-1234",
        )

        # Verify accept_request was called
        assert len(accepted_users) == 1
        assert "abc123" in accepted_users
        assert handler.accept_request.call_count == 1


@pytest.mark.asyncio
async def test_no_auto_accept_for_non_match_player():
    """Test that join requests are NOT auto-accepted for non-match players."""
    # Create mock handler
    handler = SahaRaceHandler(
        bot_instance=MagicMock(),
        logger=AsyncMock(),
        conn=AsyncMock(),
        state={},
    )

    # Mock accept_request method
    handler.accept_request = AsyncMock()

    # Set up handler data
    handler.data = {
        "name": "alttpr/test-room-1234",
        "category": {"slug": "alttpr"},
        "status": {"value": "open"},
    }

    # Mock RacetimeRoomService to return that user is NOT a match player
    with patch(
        "application.services.racetime.racetime_room_service.RacetimeRoomService"
    ) as MockService:
        mock_service_instance = AsyncMock()
        mock_service_instance.is_player_on_match = AsyncMock(return_value=(False, 1))
        MockService.return_value = mock_service_instance

        # Test with a different user (not on the match)
        await handler._handle_join_request(
            racetime_user_id="xyz999",  # Different user, not on match
            racetime_user_name="RandomPlayer",
            room_slug="alttpr/test-room-1234",
        )

        # Verify accept_request was NOT called
        assert handler.accept_request.call_count == 0


@pytest.mark.asyncio
async def test_no_auto_accept_when_no_match_found():
    """Test that join requests are NOT auto-accepted when no match is found for the room."""
    # Create mock handler
    handler = SahaRaceHandler(
        bot_instance=MagicMock(),
        logger=AsyncMock(),
        conn=AsyncMock(),
        state={},
    )

    # Mock accept_request method
    handler.accept_request = AsyncMock()

    # Set up handler data
    handler.data = {
        "name": "alttpr/unknown-room-9999",
        "category": {"slug": "alttpr"},
        "status": {"value": "open"},
    }

    # Mock RacetimeRoomService to return no match found
    with patch(
        "application.services.racetime.racetime_room_service.RacetimeRoomService"
    ) as MockService:
        mock_service_instance = AsyncMock()
        mock_service_instance.is_player_on_match = AsyncMock(return_value=(False, None))
        MockService.return_value = mock_service_instance

        # Test with no match found
        await handler._handle_join_request(
            racetime_user_id="abc123",
            racetime_user_name="Player1RT",
            room_slug="alttpr/unknown-room-9999",
        )

        # Verify accept_request was NOT called
        assert handler.accept_request.call_count == 0


@pytest.mark.asyncio
async def test_auto_accept_triggered_on_requested_status():
    """Test that auto-accept is triggered when entrant status changes to 'requested'."""
    from application.events import EventBus, RacetimeEntrantStatusChangedEvent

    # Track emitted events
    emitted_events = []

    @EventBus.on(RacetimeEntrantStatusChangedEvent)
    async def capture_event(event: RacetimeEntrantStatusChangedEvent):
        emitted_events.append(event)

    # Track accept_request calls
    accepted_users = []

    try:
        # Create handler
        handler = SahaRaceHandler(
            bot_instance=MagicMock(),
            logger=AsyncMock(),
            conn=AsyncMock(),
            state={},
        )

        # Mock accept_request
        async def track_accept(racetime_id: str):
            accepted_users.append(racetime_id)

        handler.accept_request = AsyncMock(side_effect=track_accept)

        # Mock RacetimeRoomService
        with patch(
            "application.services.racetime.racetime_room_service.RacetimeRoomService"
        ) as MockService:
            mock_service_instance = AsyncMock()
            mock_service_instance.is_player_on_match = AsyncMock(return_value=(True, 1))
            MockService.return_value = mock_service_instance

            # First call: establish baseline (user ready)
            baseline_data = {
                "race": {
                    "name": "alttpr/test-room-1234",
                    "category": {"slug": "alttpr"},
                    "status": {"value": "open"},
                    "entrants": [
                        {
                            "user": {"id": "abc123", "name": "Player1RT"},
                            "status": {"value": "not_ready"},
                        }
                    ],
                }
            }
            await handler.race_data(baseline_data)

            # Second call: user status changes to 'requested' (trying to join invitational)
            updated_data = {
                "race": {
                    "name": "alttpr/test-room-1234",
                    "category": {"slug": "alttpr"},
                    "status": {"value": "open"},
                    "entrants": [
                        {
                            "user": {"id": "abc123", "name": "Player1RT"},
                            "status": {"value": "requested"},
                        }
                    ],
                }
            }
            await handler.race_data(updated_data)

            # Verify status change event was emitted
            assert len(emitted_events) >= 1
            status_events = [e for e in emitted_events if e.new_status == "requested"]
            assert len(status_events) == 1

            # Verify accept_request was called
            assert len(accepted_users) == 1
            assert "abc123" in accepted_users

    finally:
        EventBus.clear_all()
