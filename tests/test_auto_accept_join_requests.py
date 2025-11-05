"""
Test automatic acceptance of join requests for match players.

Verifies that when a player requests to join an invitational RaceTime race room,
if they are listed as a player on the match, their request is automatically accepted.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from models import User, Permission
from models.match_schedule import Match, MatchPlayers
from racetime.client import SahaRaceHandler


@pytest.mark.asyncio
async def test_auto_accept_join_request_for_match_player():
    """Test that join requests are auto-accepted for players on the match."""
    # Create mock user with linked racetime account
    user1 = User(
        id=1,
        discord_id=111111,
        discord_username='Player1',
        racetime_id='abc123',
        racetime_name='Player1RT',
        permission=Permission.USER,
    )

    # Create mock match player
    match_player1 = MagicMock(spec=MatchPlayers)
    match_player1.user = user1

    # Create mock match
    mock_match = AsyncMock(spec=Match)
    mock_match.id = 1
    mock_match.racetime_room_slug = 'alttpr/test-room-1234'

    # Mock players relation
    mock_players = AsyncMock()
    mock_players.all = AsyncMock(return_value=AsyncMock())
    mock_players.all.return_value.prefetch_related = AsyncMock(return_value=[match_player1])
    mock_match.players = mock_players

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
        'name': 'alttpr/test-room-1234',
        'category': {'slug': 'alttpr'},
        'status': {'value': 'open'},
    }

    # Mock Match.filter to return our match
    with patch('racetime.client.Match') as MockMatch:
        mock_filter = AsyncMock()
        mock_filter.prefetch_related = MagicMock(return_value=mock_filter)
        mock_filter.first = AsyncMock(return_value=mock_match)
        MockMatch.filter = MagicMock(return_value=mock_filter)

        # Test the join request handler
        await handler._handle_join_request(
            racetime_user_id='abc123',
            racetime_user_name='Player1RT',
            room_slug='alttpr/test-room-1234',
        )

        # Verify accept_request was called
        assert len(accepted_users) == 1
        assert 'abc123' in accepted_users
        assert handler.accept_request.call_count == 1


@pytest.mark.asyncio
async def test_no_auto_accept_for_non_match_player():
    """Test that join requests are NOT auto-accepted for non-match players."""
    # Create mock user (match player)
    user1 = User(
        id=1,
        discord_id=111111,
        discord_username='Player1',
        racetime_id='abc123',
        racetime_name='Player1RT',
        permission=Permission.USER,
    )

    # Create mock match player
    match_player1 = MagicMock(spec=MatchPlayers)
    match_player1.user = user1

    # Create mock match
    mock_match = AsyncMock(spec=Match)
    mock_match.id = 1
    mock_match.racetime_room_slug = 'alttpr/test-room-1234'

    # Mock players relation
    mock_players = AsyncMock()
    mock_players.all = AsyncMock(return_value=AsyncMock())
    mock_players.all.return_value.prefetch_related = AsyncMock(return_value=[match_player1])
    mock_match.players = mock_players

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
        'name': 'alttpr/test-room-1234',
        'category': {'slug': 'alttpr'},
        'status': {'value': 'open'},
    }

    # Mock Match.filter to return our match
    with patch('racetime.client.Match') as MockMatch:
        mock_filter = AsyncMock()
        mock_filter.prefetch_related = MagicMock(return_value=mock_filter)
        mock_filter.first = AsyncMock(return_value=mock_match)
        MockMatch.filter = MagicMock(return_value=mock_filter)

        # Test with a different user (not on the match)
        await handler._handle_join_request(
            racetime_user_id='xyz999',  # Different user, not on match
            racetime_user_name='RandomPlayer',
            room_slug='alttpr/test-room-1234',
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
        'name': 'alttpr/unknown-room-9999',
        'category': {'slug': 'alttpr'},
        'status': {'value': 'open'},
    }

    # Mock Match.filter to return None (no match found)
    with patch('racetime.client.Match') as MockMatch:
        mock_filter = AsyncMock()
        mock_filter.prefetch_related = MagicMock(return_value=mock_filter)
        mock_filter.first = AsyncMock(return_value=None)
        MockMatch.filter = MagicMock(return_value=mock_filter)

        # Test with no match found
        await handler._handle_join_request(
            racetime_user_id='abc123',
            racetime_user_name='Player1RT',
            room_slug='alttpr/unknown-room-9999',
        )

        # Verify accept_request was NOT called
        assert handler.accept_request.call_count == 0


@pytest.mark.asyncio
async def test_auto_accept_triggered_on_requested_status():
    """Test that auto-accept is triggered when entrant status changes to 'requested'."""
    from application.events import EventBus, RacetimeEntrantStatusChangedEvent

    # Create mock user
    user1 = User(
        id=1,
        discord_id=111111,
        discord_username='Player1',
        racetime_id='abc123',
        racetime_name='Player1RT',
        permission=Permission.USER,
    )

    # Create mock match player
    match_player1 = MagicMock(spec=MatchPlayers)
    match_player1.user = user1

    # Create mock match
    mock_match = AsyncMock(spec=Match)
    mock_match.id = 1
    mock_match.racetime_room_slug = 'alttpr/test-room-1234'

    # Mock players relation
    mock_players = AsyncMock()
    mock_players.all = AsyncMock(return_value=AsyncMock())
    mock_players.all.return_value.prefetch_related = AsyncMock(return_value=[match_player1])
    mock_match.players = mock_players

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

        # Mock Match.filter
        with patch('racetime.client.Match') as MockMatch:
            mock_filter = AsyncMock()
            mock_filter.prefetch_related = MagicMock(return_value=mock_filter)
            mock_filter.first = AsyncMock(return_value=mock_match)
            MockMatch.filter = MagicMock(return_value=mock_filter)

            # First call: establish baseline (user ready)
            baseline_data = {
                'race': {
                    'name': 'alttpr/test-room-1234',
                    'category': {'slug': 'alttpr'},
                    'status': {'value': 'open'},
                    'entrants': [
                        {
                            'user': {'id': 'abc123', 'name': 'Player1RT'},
                            'status': {'value': 'not_ready'}
                        }
                    ]
                }
            }
            await handler.race_data(baseline_data)

            # Second call: user status changes to 'requested' (trying to join invitational)
            updated_data = {
                'race': {
                    'name': 'alttpr/test-room-1234',
                    'category': {'slug': 'alttpr'},
                    'status': {'value': 'open'},
                    'entrants': [
                        {
                            'user': {'id': 'abc123', 'name': 'Player1RT'},
                            'status': {'value': 'requested'}
                        }
                    ]
                }
            }
            await handler.race_data(updated_data)

            # Verify status change event was emitted
            assert len(emitted_events) >= 1
            status_events = [e for e in emitted_events if e.new_status == 'requested']
            assert len(status_events) == 1

            # Verify accept_request was called
            assert len(accepted_users) == 1
            assert 'abc123' in accepted_users

    finally:
        EventBus.clear_all()
