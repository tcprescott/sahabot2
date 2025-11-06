"""
Tests for RaceTime.gg status change events.

Verifies that SahaRaceHandler emits events when:
- Race status changes (open -> pending -> in_progress -> finished)
- Entrant status changes (ready -> in_progress -> done/dnf)
- Players join or leave race rooms
- Bot creates or joins race rooms
- Bot invites players to races
- Application user IDs are resolved from racetime IDs
- System actions are distinguished from unauthenticated users
"""

import pytest
from unittest.mock import AsyncMock, patch

from racetime.client import SahaRaceHandler
from application.events import (
    EventBus,
    RacetimeRaceStatusChangedEvent,
    RacetimeEntrantStatusChangedEvent,
    RacetimeEntrantJoinedEvent,
    RacetimeEntrantLeftEvent,
    RacetimeEntrantInvitedEvent,
    RacetimeBotJoinedRaceEvent,
    RacetimeBotCreatedRaceEvent,
)
from models import User, Permission, SYSTEM_USER_ID


@pytest.mark.asyncio
async def test_race_status_change_emits_event():
    """Test that race status changes emit RacetimeRaceStatusChangedEvent."""
    # Track emitted events
    emitted_events = []

    @EventBus.on(RacetimeRaceStatusChangedEvent)
    async def capture_event(event: RacetimeRaceStatusChangedEvent):
        emitted_events.append(event)

    try:
        # Create race handler with mock dependencies
        handler = SahaRaceHandler(bot_instance=AsyncMock(), 
            logger=AsyncMock(),
            conn=AsyncMock(),
            state={},
        )

        # First call: establish baseline (pending status)
        baseline_data = {
            'race': {
                'name': 'alttpr/test-race-1234',
                'category': {'slug': 'alttpr'},
                'status': {'value': 'pending'},
                'entrants': []
            }
        }
        await handler.race_data(baseline_data)

        # Second call: status change to in_progress
        updated_data = {
            'race': {
                'name': 'alttpr/test-race-1234',
                'category': {'slug': 'alttpr'},
                'status': {'value': 'in_progress'},
                'started_at': '2025-11-04T12:00:00Z',
                'entrants': []
            }
        }
        await handler.race_data(updated_data)

        # Verify event was emitted
        assert len(emitted_events) == 1, f"Expected 1 event, got {len(emitted_events)}"
        event = emitted_events[0]
        assert event.category == 'alttpr'
        assert event.room_slug == 'alttpr/test-race-1234'
        assert event.old_status == 'pending'
        assert event.new_status == 'in_progress'
        assert event.started_at == '2025-11-04T12:00:00Z'
        assert event.user_id == SYSTEM_USER_ID  # Race status changes are system automation
    finally:
        # Cleanup
        EventBus.clear_all()


@pytest.mark.asyncio
async def test_entrant_status_change_emits_event():
    """Test that entrant status changes emit RacetimeEntrantStatusChangedEvent."""
    # Track emitted events
    emitted_events = []

    @EventBus.on(RacetimeEntrantStatusChangedEvent)
    async def capture_event(event: RacetimeEntrantStatusChangedEvent):
        emitted_events.append(event)

    try:
        # Create race handler with mock dependencies
        handler = SahaRaceHandler(bot_instance=AsyncMock(), 
            logger=AsyncMock(),
            conn=AsyncMock(),
            state={},
        )

        # First call: establish baseline (race in_progress, entrant ready)
        baseline_data = {
            'race': {
                'name': 'alttpr/test-race-1234',
                'category': {'slug': 'alttpr'},
                'status': {'value': 'in_progress'},
                'entrants': [
                    {
                        'user': {'id': 'abc123', 'name': 'Player1'},
                        'status': {'value': 'ready'}
                    }
                ]
            }
        }
        await handler.race_data(baseline_data)

        # Second call: entrant status change to in_progress
        updated_data = {
            'race': {
                'name': 'alttpr/test-race-1234',
                'category': {'slug': 'alttpr'},
                'status': {'value': 'in_progress'},
                'entrants': [
                    {
                        'user': {'id': 'abc123', 'name': 'Player1'},
                        'status': {'value': 'in_progress'}
                    }
                ]
            }
        }
        await handler.race_data(updated_data)

        # Verify event was emitted
        assert len(emitted_events) >= 1, f"Expected at least 1 event, got {len(emitted_events)}"
        # Find the entrant status change event (may have race status event too)
        entrant_events = [e for e in emitted_events if isinstance(e, RacetimeEntrantStatusChangedEvent)]
        assert len(entrant_events) == 1
        event = entrant_events[0]
        assert event.category == 'alttpr'
        assert event.room_slug == 'alttpr/test-race-1234'
        assert event.racetime_user_id == 'abc123'
        assert event.racetime_user_name == 'Player1'
        assert event.old_status == 'ready'
        assert event.new_status == 'in_progress'
    finally:
        # Cleanup
        EventBus.clear_all()


@pytest.mark.asyncio
async def test_entrant_finish_includes_placement():
    """Test that finish events include placement and finish_time."""
    # Track emitted events
    emitted_events = []

    @EventBus.on(RacetimeEntrantStatusChangedEvent)
    async def capture_event(event: RacetimeEntrantStatusChangedEvent):
        emitted_events.append(event)

    try:
        # Create race handler with mock dependencies
        handler = SahaRaceHandler(bot_instance=AsyncMock(), 
            logger=AsyncMock(),
            conn=AsyncMock(),
            state={},
        )

        # First call: establish baseline (entrant in_progress)
        baseline_data = {
            'race': {
                'name': 'alttpr/test-race-1234',
                'category': {'slug': 'alttpr'},
                'status': {'value': 'in_progress'},
                'entrants': [
                    {
                        'user': {'id': 'abc123', 'name': 'Player1'},
                        'status': {'value': 'in_progress'}
                    }
                ]
            }
        }
        await handler.race_data(baseline_data)

        # Second call: entrant finishes
        updated_data = {
            'race': {
                'name': 'alttpr/test-race-1234',
                'category': {'slug': 'alttpr'},
                'status': {'value': 'in_progress'},
                'entrants': [
                    {
                        'user': {'id': 'abc123', 'name': 'Player1'},
                        'status': {'value': 'done'},
                        'place': 1,
                        'finish_time': 'PT1H23M45S'  # ISO 8601 duration
                    }
                ]
            }
        }
        await handler.race_data(updated_data)

        # Verify event was emitted with placement data
        assert len(emitted_events) == 1
        event = emitted_events[0]
        assert event.new_status == 'done'
        assert event.place == 1
        assert event.finish_time == 'PT1H23M45S'
    finally:
        # Cleanup
        EventBus.clear_all()


@pytest.mark.asyncio
async def test_entrant_join_emits_event():
    """Test that players joining emit RacetimeEntrantJoinedEvent."""
    emitted_events = []

    @EventBus.on(RacetimeEntrantJoinedEvent)
    async def capture_event(event: RacetimeEntrantJoinedEvent):
        emitted_events.append(event)

    try:
        handler = SahaRaceHandler(bot_instance=AsyncMock(), 
            logger=AsyncMock(),
            conn=AsyncMock(),
            state={},
        )

        # First call: race with no entrants
        baseline_data = {
            'race': {
                'name': 'alttpr/test-race-1234',
                'category': {'slug': 'alttpr'},
                'status': {'value': 'open'},
                'entrants': []
            }
        }
        await handler.race_data(baseline_data)

        # Second call: new player joins
        updated_data = {
            'race': {
                'name': 'alttpr/test-race-1234',
                'category': {'slug': 'alttpr'},
                'status': {'value': 'open'},
                'entrants': [
                    {
                        'user': {'id': 'abc123', 'name': 'Player1'},
                        'status': {'value': 'not_ready'}
                    }
                ]
            }
        }
        await handler.race_data(updated_data)

        # Verify join event was emitted
        assert len(emitted_events) == 1
        event = emitted_events[0]
        assert event.racetime_user_id == 'abc123'
        assert event.racetime_user_name == 'Player1'
        assert event.initial_status == 'not_ready'
        assert event.room_slug == 'alttpr/test-race-1234'
    finally:
        EventBus.clear_all()


@pytest.mark.asyncio
async def test_entrant_leave_emits_event():
    """Test that players leaving emit RacetimeEntrantLeftEvent."""
    emitted_events = []

    @EventBus.on(RacetimeEntrantLeftEvent)
    async def capture_event(event: RacetimeEntrantLeftEvent):
        emitted_events.append(event)

    try:
        handler = SahaRaceHandler(bot_instance=AsyncMock(), 
            logger=AsyncMock(),
            conn=AsyncMock(),
            state={},
        )

        # First call: race with one entrant
        baseline_data = {
            'race': {
                'name': 'alttpr/test-race-1234',
                'category': {'slug': 'alttpr'},
                'status': {'value': 'open'},
                'entrants': [
                    {
                        'user': {'id': 'abc123', 'name': 'Player1'},
                        'status': {'value': 'not_ready'}
                    }
                ]
            }
        }
        await handler.race_data(baseline_data)

        # Second call: player leaves
        updated_data = {
            'race': {
                'name': 'alttpr/test-race-1234',
                'category': {'slug': 'alttpr'},
                'status': {'value': 'open'},
                'entrants': []
            }
        }
        await handler.race_data(updated_data)

        # Verify leave event was emitted
        assert len(emitted_events) == 1
        event = emitted_events[0]
        assert event.racetime_user_id == 'abc123'
        assert event.racetime_user_name == 'Player1'
        assert event.last_status == 'not_ready'
        assert event.room_slug == 'alttpr/test-race-1234'
    finally:
        EventBus.clear_all()


@pytest.mark.asyncio
async def test_bot_invite_emits_event():
    """Test that bot inviting a player emits RacetimeEntrantInvitedEvent."""
    emitted_events = []

    @EventBus.on(RacetimeEntrantInvitedEvent)
    async def capture_event(event: RacetimeEntrantInvitedEvent):
        emitted_events.append(event)

    try:
        # Mock websocket
        mock_ws = AsyncMock()
        
        handler = SahaRaceHandler(bot_instance=AsyncMock(), 
            logger=AsyncMock(),
            conn=AsyncMock(),
            state={},
        )
        
        # Set up handler data and mock websocket
        handler.data = {
            'name': 'alttpr/test-race-1234',
            'category': {'slug': 'alttpr'},
            'status': {'value': 'invitational'},
        }
        handler.ws = mock_ws  # Mock the websocket connection

        # Invite a user
        await handler.invite_user('user123')

        # Verify invite event was emitted
        assert len(emitted_events) == 1
        event = emitted_events[0]
        assert event.racetime_user_id == 'user123'
        assert event.room_slug == 'alttpr/test-race-1234'
        assert event.category == 'alttpr'
        
        # Verify websocket was called
        assert mock_ws.send.called
    finally:
        EventBus.clear_all()


@pytest.mark.asyncio
async def test_bot_joined_race_emits_event():
    """Test that bot joining existing race emits RacetimeBotJoinedRaceEvent."""
    emitted_events = []

    @EventBus.on(RacetimeBotJoinedRaceEvent)
    async def capture_event(event: RacetimeBotJoinedRaceEvent):
        emitted_events.append(event)

    try:
        handler = SahaRaceHandler(bot_instance=AsyncMock(), 
            logger=AsyncMock(),
            conn=AsyncMock(),
            state={},
        )
        
        # Set up handler data (bot joining existing race)
        handler.data = {
            'name': 'alttpr/test-race-1234',
            'category': {'slug': 'alttpr'},
            'status': {'value': 'open'},
            'entrants': [
                {'user': {'id': 'player1', 'name': 'Player1'}, 'status': {'value': 'not_ready'}},
                {'user': {'id': 'player2', 'name': 'Player2'}, 'status': {'value': 'ready'}},
            ]
        }
        handler._bot_created_room = False  # Bot joined (didn't create)

        # Call begin which emits the event
        await handler.begin()

        # Verify bot joined event was emitted
        assert len(emitted_events) == 1
        event = emitted_events[0]
        assert event.room_slug == 'alttpr/test-race-1234'
        assert event.category == 'alttpr'
        assert event.race_status == 'open'
        assert event.entrant_count == 2
        assert event.bot_action == 'join'
        assert event.user_id == SYSTEM_USER_ID  # System automation action
    finally:
        EventBus.clear_all()


@pytest.mark.asyncio
async def test_bot_created_race_emits_event():
    """Test that bot creating race emits RacetimeBotCreatedRaceEvent."""
    emitted_events = []

    @EventBus.on(RacetimeBotCreatedRaceEvent)
    async def capture_event(event: RacetimeBotCreatedRaceEvent):
        emitted_events.append(event)

    try:
        handler = SahaRaceHandler(bot_instance=AsyncMock(), 
            logger=AsyncMock(),
            conn=AsyncMock(),
            state={},
        )
        
        # Set up handler data (bot created this race)
        handler.data = {
            'name': 'alttpr/test-race-1234',
            'category': {'slug': 'alttpr'},
            'status': {'value': 'open'},
            'goal': {'name': 'Beat the game'},
            'unlisted': False,
            'entrants': []
        }
        handler._bot_created_room = True  # Bot created this room

        # Call begin which emits the event
        await handler.begin()

        # Verify bot created event was emitted
        assert len(emitted_events) == 1
        event = emitted_events[0]
        assert event.room_slug == 'alttpr/test-race-1234'
        assert event.category == 'alttpr'
        assert event.goal == 'Beat the game'
        assert event.invitational is True  # unlisted=False means invitational=True
        assert event.bot_action == 'create'
        assert event.user_id == SYSTEM_USER_ID  # System automation action
    finally:
        EventBus.clear_all()


@pytest.mark.asyncio
async def test_user_id_lookup_from_racetime_id():
    """Test that events include application user_id when racetime account is linked."""
    emitted_events = []

    @EventBus.on(RacetimeEntrantJoinedEvent)
    async def capture_join_event(event: RacetimeEntrantJoinedEvent):
        emitted_events.append(('join', event))

    @EventBus.on(RacetimeEntrantStatusChangedEvent)
    async def capture_status_event(event: RacetimeEntrantStatusChangedEvent):
        emitted_events.append(('status', event))

    @EventBus.on(RacetimeEntrantInvitedEvent)
    async def capture_invite_event(event: RacetimeEntrantInvitedEvent):
        emitted_events.append(('invite', event))

    try:
        # Create mock user with linked racetime account
        mock_user = User(
            id=42,
            discord_id=123456789,
            discord_username='TestUser',
            racetime_id='abc123',  # Linked racetime account
            racetime_name='Player1',
            permission=Permission.USER,
        )

        # Create handler first
        handler = SahaRaceHandler(bot_instance=AsyncMock(), 
            logger=AsyncMock(),
            conn=AsyncMock(),
            state={},
        )

        # Mock the repository instance's method to return our user for abc123, None for others
        async def mock_get_by_racetime_id(racetime_id: str):
            if racetime_id == 'abc123':
                return mock_user
            return None

        with patch.object(handler._user_repository, 'get_by_racetime_id', side_effect=mock_get_by_racetime_id):

            # Test 1: Join event with linked user
            baseline_data = {
                'race': {
                    'name': 'alttpr/test-race-1234',
                    'category': {'slug': 'alttpr'},
                    'status': {'value': 'open'},
                    'entrants': []
                }
            }
            await handler.race_data(baseline_data)

            updated_data = {
                'race': {
                    'name': 'alttpr/test-race-1234',
                    'category': {'slug': 'alttpr'},
                    'status': {'value': 'open'},
                    'entrants': [
                        {
                            'user': {'id': 'abc123', 'name': 'Player1'},
                            'status': {'value': 'not_ready'}
                        }
                    ]
                }
            }
            await handler.race_data(updated_data)

            # Verify join event has user_id
            join_events = [e for t, e in emitted_events if t == 'join']
            assert len(join_events) == 1
            assert join_events[0].user_id == 42
            assert join_events[0].racetime_user_id == 'abc123'

            # Test 2: Status change event with linked user
            status_change_data = {
                'race': {
                    'name': 'alttpr/test-race-1234',
                    'category': {'slug': 'alttpr'},
                    'status': {'value': 'open'},
                    'entrants': [
                        {
                            'user': {'id': 'abc123', 'name': 'Player1'},
                            'status': {'value': 'ready'}
                        }
                    ]
                }
            }
            await handler.race_data(status_change_data)

            # Verify status event has user_id
            status_events = [e for t, e in emitted_events if t == 'status']
            assert len(status_events) == 1
            assert status_events[0].user_id == 42
            assert status_events[0].racetime_user_id == 'abc123'

            # Test 3: Invite event with linked user
            handler.data = {
                'name': 'alttpr/test-race-1234',
                'category': {'slug': 'alttpr'},
                'status': {'value': 'invitational'},
            }
            handler.ws = AsyncMock()
            await handler.invite_user('abc123')

            # Verify invite event has user_id
            invite_events = [e for t, e in emitted_events if t == 'invite']
            assert len(invite_events) == 1
            assert invite_events[0].user_id == 42
            assert invite_events[0].racetime_user_id == 'abc123'

    finally:
        EventBus.clear_all()


@pytest.mark.asyncio
async def test_user_id_none_when_not_linked():
    """Test that events have user_id=None when racetime account is not linked."""
    emitted_events = []

    @EventBus.on(RacetimeEntrantJoinedEvent)
    async def capture_event(event: RacetimeEntrantJoinedEvent):
        emitted_events.append(event)

    try:
        # Mock repository to return None (no linked account)
        async def mock_get_by_racetime_id(racetime_id: str):
            return None

        with patch('application.repositories.user_repository.UserRepository') as MockRepo:
            mock_repo_instance = AsyncMock()
            mock_repo_instance.get_by_racetime_id = mock_get_by_racetime_id
            MockRepo.return_value = mock_repo_instance

            handler = SahaRaceHandler(bot_instance=AsyncMock(), 
                logger=AsyncMock(),
                conn=AsyncMock(),
                state={},
            )

            # Baseline
            baseline_data = {
                'race': {
                    'name': 'alttpr/test-race-1234',
                    'category': {'slug': 'alttpr'},
                    'status': {'value': 'open'},
                    'entrants': []
                }
            }
            await handler.race_data(baseline_data)

            # Player with unlinked account joins
            updated_data = {
                'race': {
                    'name': 'alttpr/test-race-1234',
                    'category': {'slug': 'alttpr'},
                    'status': {'value': 'open'},
                    'entrants': [
                        {
                            'user': {'id': 'xyz999', 'name': 'UnlinkedPlayer'},
                            'status': {'value': 'not_ready'}
                        }
                    ]
                }
            }
            await handler.race_data(updated_data)

            # Verify event has user_id=None
            assert len(emitted_events) == 1
            event = emitted_events[0]
            assert event.user_id is None
            assert event.racetime_user_id == 'xyz999'
            assert event.racetime_user_name == 'UnlinkedPlayer'

    finally:
        EventBus.clear_all()
