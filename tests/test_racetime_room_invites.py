"""
Test RaceTime room creation with automatic player invitations.

Verifies that when a RaceTime room is created for a match,
all players with linked RaceTime accounts are automatically invited.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from models import User, Permission
from models.match_schedule import Match, Tournament, MatchPlayers
from application.services.tournaments.tournament_service import TournamentService


@pytest.mark.asyncio
async def test_create_room_invites_linked_players(db, admin_user, sample_organization):
    """Test that room creation invites all players with linked RaceTime accounts."""

    # Create mock users
    user1 = User(
        id=1,
        discord_id=111111,
        discord_username='Player1',
        racetime_id='abc123',  # Has linked account
        racetime_name='Player1RT',
        permission=Permission.USER,
    )

    user2 = User(
        id=2,
        discord_id=222222,
        discord_username='Player2',
        racetime_id='def456',  # Has linked account
        racetime_name='Player2RT',
        permission=Permission.USER,
    )

    user3 = User(
        id=3,
        discord_id=333333,
        discord_username='Player3',
        racetime_id=None,  # No linked account
        racetime_name=None,
        permission=Permission.USER,
    )

    # Create mock match players
    match_player1 = MagicMock(spec=MatchPlayers)
    match_player1.user = user1
    match_player2 = MagicMock(spec=MatchPlayers)
    match_player2.user = user2
    match_player3 = MagicMock(spec=MatchPlayers)
    match_player3.user = user3

    # Track invite calls
    invited_users = []

    # Mock handler with invite_user method
    mock_handler = AsyncMock()
    mock_handler.data = {'name': 'alttpr/test-room-1234'}

    async def track_invite(racetime_id: str):
        """Track which users were invited."""
        invited_users.append(racetime_id)

    mock_handler.invite_user = AsyncMock(side_effect=track_invite)

    # Mock the match
    mock_match = AsyncMock(spec=Match)
    mock_match.id = 1
    mock_match.racetime_room_slug = None
    mock_match.racetime_goal = None
    mock_match.racetime_invitational = True
    mock_match.title = "Test Match"
    mock_match.save = AsyncMock()

    # Mock players relation
    mock_players = AsyncMock()
    mock_prefetch_result = AsyncMock()
    mock_prefetch_result.all = AsyncMock(return_value=[match_player1, match_player2, match_player3])
    mock_players.prefetch_related = MagicMock(return_value=mock_prefetch_result)
    mock_match.players = mock_players

    # Mock tournament
    mock_tournament = AsyncMock(spec=Tournament)
    mock_tournament.id = 1
    mock_tournament.organization_id = 1
    mock_tournament.racetime_bot_id = 1
    mock_tournament.racetime_default_goal = "Beat the game"
    mock_tournament.race_room_profile_id = None
    mock_match.tournament = mock_tournament

    # Mock racetime bot
    mock_bot_config = MagicMock()
    mock_bot_config.category = 'alttpr'
    mock_bot_config.client_id = 'test_client'
    mock_bot_config.client_secret = 'test_secret'
    mock_bot_config.id = 1
    mock_bot_config.is_active = True
    mock_tournament.racetime_bot = mock_bot_config

    # Mock the service
    with patch('application.services.tournaments.tournament_service.Match') as MockMatch, \
         patch('racetime.client.RacetimeBot') as MockBot, \
         patch('aiohttp.ClientSession') as MockSession:

        # Setup Match.filter mock
        mock_filter = AsyncMock()
        mock_filter.select_related = MagicMock(return_value=mock_filter)
        mock_filter.prefetch_related = MagicMock(return_value=mock_filter)
        mock_filter.first = AsyncMock(return_value=mock_match)
        MockMatch.filter = MagicMock(return_value=mock_filter)

        # Setup RacetimeBot mock
        mock_bot_instance = MagicMock()
        mock_bot_instance.http = None
        mock_bot_instance.access_token = 'test_token'
        mock_bot_instance.reauthorize_every = 3600
        mock_bot_instance.authorize = MagicMock(return_value=('test_token', 3600))
        mock_bot_instance.startrace = AsyncMock(return_value=mock_handler)
        MockBot.return_value = mock_bot_instance

        # Setup aiohttp session mock
        mock_session_instance = MagicMock()
        mock_session_instance.close = AsyncMock()
        mock_session_instance.closed = False
        MockSession.return_value = mock_session_instance

        service = TournamentService()

        # Mock authorization checks
        service.org_service.user_can_manage_tournaments = AsyncMock(return_value=True)

        # Create the room
        result = await service.create_racetime_room(
            user=admin_user,
            organization_id=sample_organization.id,
            match_id=1,
        )

        # Verify room was created
        assert result is not None
        assert result.racetime_room_slug == 'alttpr/test-room-1234'

        # Verify invites were sent
        # Should invite user1 (abc123) and user2 (def456), but NOT user3 (no racetime_id)
        assert len(invited_users) == 2
        assert 'abc123' in invited_users
        assert 'def456' in invited_users

        # Verify invite_user was called twice
        assert mock_handler.invite_user.call_count == 2


@pytest.mark.asyncio
async def test_create_room_handles_invite_failure(db, admin_user, sample_organization):
    """Test that individual invite failures don't stop other invites."""
    # Create mock users
    user1 = User(
        id=1,
        discord_id=111111,
        discord_username='Player1',
        racetime_id='abc123',
        racetime_name='Player1RT',
        permission=Permission.USER,
    )

    user2 = User(
        id=2,
        discord_id=222222,
        discord_username='Player2',
        racetime_id='def456',
        racetime_name='Player2RT',
        permission=Permission.USER,
    )

    # Create mock match players
    match_player1 = MagicMock(spec=MatchPlayers)
    match_player1.user = user1
    match_player2 = MagicMock(spec=MatchPlayers)
    match_player2.user = user2

    # Track invite calls
    invited_users = []
    failed_users = []

    # Mock handler that fails on first invite
    mock_handler = AsyncMock()
    mock_handler.data = {'name': 'alttpr/test-room-5678'}

    async def track_invite(racetime_id: str):
        """Track invites and fail on first one."""
        if racetime_id == 'abc123':
            failed_users.append(racetime_id)
            raise Exception("Network error")
        invited_users.append(racetime_id)

    mock_handler.invite_user = AsyncMock(side_effect=track_invite)

    # Mock the match
    mock_match = AsyncMock(spec=Match)
    mock_match.id = 2
    mock_match.racetime_room_slug = None
    mock_match.racetime_goal = None
    mock_match.racetime_invitational = True
    mock_match.title = "Test Match 2"
    mock_match.save = AsyncMock()

    # Mock players relation
    mock_players = AsyncMock()
    mock_prefetch_result = AsyncMock()
    mock_prefetch_result.all = AsyncMock(return_value=[match_player1, match_player2])
    mock_players.prefetch_related = MagicMock(return_value=mock_prefetch_result)
    mock_match.players = mock_players

    # Mock tournament
    mock_tournament = AsyncMock(spec=Tournament)
    mock_tournament.id = 1
    mock_tournament.organization_id = 1
    mock_tournament.racetime_bot_id = 1
    mock_tournament.racetime_default_goal = "Beat the game"
    mock_tournament.race_room_profile_id = None
    mock_match.tournament = mock_tournament

    # Mock racetime bot
    mock_bot_config = MagicMock()
    mock_bot_config.category = 'alttpr'
    mock_bot_config.client_id = 'test_client'
    mock_bot_config.client_secret = 'test_secret'
    mock_bot_config.id = 1
    mock_bot_config.is_active = True
    mock_tournament.racetime_bot = mock_bot_config

    # Mock the service
    with patch('application.services.tournaments.tournament_service.Match') as MockMatch, \
         patch('racetime.client.RacetimeBot') as MockBot, \
         patch('aiohttp.ClientSession') as MockSession:

        # Setup Match.filter mock
        mock_filter = AsyncMock()
        mock_filter.select_related = MagicMock(return_value=mock_filter)
        mock_filter.prefetch_related = MagicMock(return_value=mock_filter)
        mock_filter.first = AsyncMock(return_value=mock_match)
        MockMatch.filter = MagicMock(return_value=mock_filter)

        # Setup RacetimeBot mock
        mock_bot_instance = MagicMock()
        mock_bot_instance.http = None
        mock_bot_instance.access_token = 'test_token'
        mock_bot_instance.reauthorize_every = 3600
        mock_bot_instance.authorize = MagicMock(return_value=('test_token', 3600))
        mock_bot_instance.startrace = AsyncMock(return_value=mock_handler)
        MockBot.return_value = mock_bot_instance

        # Setup aiohttp session mock
        mock_session_instance = MagicMock()
        mock_session_instance.close = AsyncMock()
        mock_session_instance.closed = False
        MockSession.return_value = mock_session_instance

        # Import and call the service method
        service = TournamentService()

        # Mock authorization checks
        service.org_service.user_can_manage_tournaments = AsyncMock(return_value=True)

        # Create the room
        result = await service.create_racetime_room(
            user=admin_user,
            organization_id=sample_organization.id,
            match_id=2,
        )

        # Verify room was still created successfully
        assert result is not None
        assert result.racetime_room_slug == 'alttpr/test-room-5678'

        # Verify second invite succeeded even though first failed
        assert len(invited_users) == 1
        assert 'def456' in invited_users
        assert len(failed_users) == 1
        assert 'abc123' in failed_users

        # Both invites should have been attempted
        assert mock_handler.invite_user.call_count == 2
