"""
Unit tests for racetime bot action methods.

Tests that the bot action wrapper methods properly:
- Call the parent implementation
- Emit appropriate events
- Log actions correctly
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch, call
from racetime.client import SahaRaceHandler
from application.events import EventBus, RacetimeBotActionEvent
from models import SYSTEM_USER_ID


@pytest.fixture
def mock_handler():
    """Create a mock race handler with necessary attributes."""
    # Create a mock bot instance
    mock_bot = MagicMock()
    
    handler = SahaRaceHandler(
        bot_instance=mock_bot,
        logger=MagicMock(),
        conn=MagicMock(),
        state={},
    )
    
    # Mock race data
    handler.data = {
        'name': 'alttpr/cool-doge-1234',
        'category': {'slug': 'alttpr'},
        'status': {'value': 'open'},
    }
    
    # Mock bot reference
    handler.bot = mock_bot
    
    # Mock WebSocket
    handler.ws = AsyncMock()
    
    return handler


@pytest.mark.asyncio
async def test_force_start_emits_event(mock_handler):
    """Test that force_start emits RacetimeBotActionEvent."""
    with patch.object(EventBus, 'emit', new_callable=AsyncMock) as mock_emit:
        await mock_handler.force_start()
        
        # Verify event was emitted
        mock_emit.assert_called_once()
        event = mock_emit.call_args[0][0]
        
        assert isinstance(event, RacetimeBotActionEvent)
        assert event.action_type == "force_start"
        assert event.room_slug == "alttpr/cool-doge-1234"
        assert event.category == "alttpr"
        assert event.user_id == SYSTEM_USER_ID


@pytest.mark.asyncio
async def test_force_unready_emits_event(mock_handler):
    """Test that force_unready emits RacetimeBotActionEvent."""
    with patch.object(EventBus, 'emit', new_callable=AsyncMock) as mock_emit:
        await mock_handler.force_unready("test_user_id")
        
        # Verify event was emitted
        mock_emit.assert_called_once()
        event = mock_emit.call_args[0][0]
        
        assert isinstance(event, RacetimeBotActionEvent)
        assert event.action_type == "force_unready"
        assert event.target_user_id == "test_user_id"
        assert event.room_slug == "alttpr/cool-doge-1234"


@pytest.mark.asyncio
async def test_remove_entrant_emits_event(mock_handler):
    """Test that remove_entrant emits RacetimeBotActionEvent."""
    with patch.object(EventBus, 'emit', new_callable=AsyncMock) as mock_emit:
        await mock_handler.remove_entrant("test_user_id")
        
        # Verify event was emitted
        mock_emit.assert_called_once()
        event = mock_emit.call_args[0][0]
        
        assert isinstance(event, RacetimeBotActionEvent)
        assert event.action_type == "remove_entrant"
        assert event.target_user_id == "test_user_id"


@pytest.mark.asyncio
async def test_cancel_race_emits_event(mock_handler):
    """Test that cancel_race emits RacetimeBotActionEvent."""
    with patch.object(EventBus, 'emit', new_callable=AsyncMock) as mock_emit:
        await mock_handler.cancel_race()
        
        # Verify event was emitted
        mock_emit.assert_called_once()
        event = mock_emit.call_args[0][0]
        
        assert isinstance(event, RacetimeBotActionEvent)
        assert event.action_type == "cancel_race"
        assert event.user_id == SYSTEM_USER_ID


@pytest.mark.asyncio
async def test_add_monitor_emits_event(mock_handler):
    """Test that add_monitor emits RacetimeBotActionEvent."""
    with patch.object(EventBus, 'emit', new_callable=AsyncMock) as mock_emit:
        await mock_handler.add_monitor("test_user_id")
        
        # Verify event was emitted
        mock_emit.assert_called_once()
        event = mock_emit.call_args[0][0]
        
        assert isinstance(event, RacetimeBotActionEvent)
        assert event.action_type == "add_monitor"
        assert event.target_user_id == "test_user_id"


@pytest.mark.asyncio
async def test_remove_monitor_emits_event(mock_handler):
    """Test that remove_monitor emits RacetimeBotActionEvent."""
    with patch.object(EventBus, 'emit', new_callable=AsyncMock) as mock_emit:
        await mock_handler.remove_monitor("test_user_id")
        
        # Verify event was emitted
        mock_emit.assert_called_once()
        event = mock_emit.call_args[0][0]
        
        assert isinstance(event, RacetimeBotActionEvent)
        assert event.action_type == "remove_monitor"
        assert event.target_user_id == "test_user_id"


@pytest.mark.asyncio
async def test_pin_message_emits_event(mock_handler):
    """Test that pin_message emits RacetimeBotActionEvent."""
    with patch.object(EventBus, 'emit', new_callable=AsyncMock) as mock_emit:
        await mock_handler.pin_message("message_hash_123")
        
        # Verify event was emitted
        mock_emit.assert_called_once()
        event = mock_emit.call_args[0][0]
        
        assert isinstance(event, RacetimeBotActionEvent)
        assert event.action_type == "pin_message"
        assert event.details == "message_hash_123"


@pytest.mark.asyncio
async def test_unpin_message_emits_event(mock_handler):
    """Test that unpin_message emits RacetimeBotActionEvent."""
    with patch.object(EventBus, 'emit', new_callable=AsyncMock) as mock_emit:
        await mock_handler.unpin_message("message_hash_123")
        
        # Verify event was emitted
        mock_emit.assert_called_once()
        event = mock_emit.call_args[0][0]
        
        assert isinstance(event, RacetimeBotActionEvent)
        assert event.action_type == "unpin_message"
        assert event.details == "message_hash_123"


@pytest.mark.asyncio
async def test_set_raceinfo_emits_event(mock_handler):
    """Test that set_raceinfo emits RacetimeBotActionEvent."""
    with patch.object(EventBus, 'emit', new_callable=AsyncMock) as mock_emit:
        await mock_handler.set_raceinfo("Test info", overwrite=True, prefix=False)
        
        # Verify event was emitted
        mock_emit.assert_called_once()
        event = mock_emit.call_args[0][0]
        
        assert isinstance(event, RacetimeBotActionEvent)
        assert event.action_type == "set_raceinfo"
        assert "overwrite=True" in event.details
        assert "prefix=False" in event.details


@pytest.mark.asyncio
async def test_set_bot_raceinfo_emits_event(mock_handler):
    """Test that set_bot_raceinfo emits RacetimeBotActionEvent."""
    with patch.object(EventBus, 'emit', new_callable=AsyncMock) as mock_emit:
        await mock_handler.set_bot_raceinfo("Bot info text")
        
        # Verify event was emitted
        mock_emit.assert_called_once()
        event = mock_emit.call_args[0][0]
        
        assert isinstance(event, RacetimeBotActionEvent)
        assert event.action_type == "set_bot_raceinfo"


@pytest.mark.asyncio
async def test_set_open_emits_event(mock_handler):
    """Test that set_open emits RacetimeBotActionEvent."""
    with patch.object(EventBus, 'emit', new_callable=AsyncMock) as mock_emit:
        await mock_handler.set_open()
        
        # Verify event was emitted
        mock_emit.assert_called_once()
        event = mock_emit.call_args[0][0]
        
        assert isinstance(event, RacetimeBotActionEvent)
        assert event.action_type == "set_open"


@pytest.mark.asyncio
async def test_set_invitational_emits_event(mock_handler):
    """Test that set_invitational emits RacetimeBotActionEvent."""
    with patch.object(EventBus, 'emit', new_callable=AsyncMock) as mock_emit:
        await mock_handler.set_invitational()
        
        # Verify event was emitted
        mock_emit.assert_called_once()
        event = mock_emit.call_args[0][0]
        
        assert isinstance(event, RacetimeBotActionEvent)
        assert event.action_type == "set_invitational"


@pytest.mark.asyncio
async def test_force_start_calls_parent(mock_handler):
    """Test that force_start calls the parent implementation."""
    with patch.object(EventBus, 'emit', new_callable=AsyncMock):
        # Mock the parent class method
        with patch('racetime_bot.RaceHandler.force_start', new_callable=AsyncMock) as mock_parent:
            await mock_handler.force_start()
            
            # Verify parent was called
            mock_parent.assert_called_once()


@pytest.mark.asyncio
async def test_event_contains_correct_room_info(mock_handler):
    """Test that events contain correct room information."""
    with patch.object(EventBus, 'emit', new_callable=AsyncMock) as mock_emit:
        await mock_handler.force_start()
        
        event = mock_emit.call_args[0][0]
        
        # Verify room information
        assert event.room_slug == "alttpr/cool-doge-1234"
        assert event.room_name == "cool-doge-1234"
        assert event.category == "alttpr"
        assert event.entity_id == "alttpr/cool-doge-1234"
