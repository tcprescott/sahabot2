"""
Unit tests for Avianart RaceTime.gg command in ALTTPR handler.

Tests the ex_avianart method that processes !avianart commands in race rooms.
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from application.services.randomizer.randomizer_service import RandomizerResult
from racetime.alttpr_handler import ALTTPRRaceHandler


class TestAvianartCommand:
    """Test suite for Avianart command in ALTTPR handler."""

    @pytest.fixture
    def mock_handler(self):
        """Create a mock handler with just the method we're testing."""
        # Create a mock object with send_message method
        handler = MagicMock()
        handler.send_message = AsyncMock()
        handler.data = {
            'status': {'value': 'open'},
            'goal': {'name': 'Test Race'},
            'entrants': []
        }

        # Bind the actual ex_avianart method to our mock
        handler.ex_avianart = ALTTPRRaceHandler.ex_avianart.__get__(handler, ALTTPRRaceHandler)

        return handler

    @pytest.fixture
    def mock_message(self):
        """Mock message data."""
        return {
            'user': {
                'id': 'test_user_123',
                'name': 'TestUser'
            }
        }

    @pytest.fixture
    def mock_result(self):
        """Mock RandomizerResult."""
        return RandomizerResult(
            url='https://avianart.games/perm/test_hash',
            hash_id='test_hash',
            settings={'preset': 'test-preset', 'race': True},
            randomizer='avianart',
            permalink='https://avianart.games/perm/test_hash',
            metadata={
                'file_select_code': ['Bow', 'Bombs', 'Hookshot', 'Mushroom', 'Lamp'],
                'version': '1.0.0',
                'preset': 'test-preset'
            }
        )

    @pytest.mark.asyncio
    async def test_ex_avianart_success(
        self,
        mock_handler,
        mock_message,
        mock_result
    ):
        """Test successful Avianart seed generation."""
        with patch('application.services.randomizer.avianart_service.AvianartService') as mock_service_class:
            mock_service = AsyncMock()
            mock_service.generate.return_value = mock_result
            mock_service_class.return_value = mock_service

            await mock_handler.ex_avianart(['test-preset'], mock_message)

            # Verify service was called correctly
            mock_service.generate.assert_called_once_with(
                preset='test-preset',
                race=True
            )

            # Verify messages were sent
            assert mock_handler.send_message.call_count == 2
            calls = [call[0][0] for call in mock_handler.send_message.call_args_list]
            
            # First message is "Generating..."
            assert 'Generating' in calls[0]
            
            # Second message has URL and code
            assert 'https://avianart.games/perm/test_hash' in calls[1]
            assert 'Bow/Bombs/Hookshot/Mushroom/Lamp' in calls[1]
            assert '1.0.0' in calls[1]

    @pytest.mark.asyncio
    async def test_ex_avianart_no_args(
        self,
        mock_handler,
        mock_message
    ):
        """Test !avianart without preset name."""
        await mock_handler.ex_avianart([], mock_message)

        mock_handler.send_message.assert_called_once()
        call_arg = mock_handler.send_message.call_args[0][0]
        assert 'Usage: !avianart <preset_name>' in call_arg

    @pytest.mark.asyncio
    async def test_ex_avianart_value_error(
        self,
        mock_handler,
        mock_message
    ):
        """Test handling of ValueError (invalid preset)."""
        with patch('application.services.randomizer.avianart_service.AvianartService') as mock_service_class:
            mock_service = AsyncMock()
            mock_service.generate.side_effect = ValueError("Invalid preset configuration")
            mock_service_class.return_value = mock_service

            await mock_handler.ex_avianart(['invalid-preset'], mock_message)

            # Should send "Generating..." then error message
            assert mock_handler.send_message.call_count == 2
            error_msg = mock_handler.send_message.call_args[0][0]
            assert 'Error: Invalid preset configuration' in error_msg

    @pytest.mark.asyncio
    async def test_ex_avianart_timeout(
        self,
        mock_handler,
        mock_message
    ):
        """Test handling of TimeoutError."""
        with patch('application.services.randomizer.avianart_service.AvianartService') as mock_service_class:
            mock_service = AsyncMock()
            mock_service.generate.side_effect = TimeoutError("Generation timed out")
            mock_service_class.return_value = mock_service

            await mock_handler.ex_avianart(['test-preset'], mock_message)

            # Should send "Generating..." then timeout message
            assert mock_handler.send_message.call_count == 2
            error_msg = mock_handler.send_message.call_args[0][0]
            assert 'timed out' in error_msg.lower()

    @pytest.mark.asyncio
    async def test_ex_avianart_generic_exception(
        self,
        mock_handler,
        mock_message
    ):
        """Test handling of generic exceptions."""
        with patch('application.services.randomizer.avianart_service.AvianartService') as mock_service_class:
            mock_service = AsyncMock()
            mock_service.generate.side_effect = Exception("Unexpected error")
            mock_service_class.return_value = mock_service

            await mock_handler.ex_avianart(['test-preset'], mock_message)

            # Should send "Generating..." then error message
            assert mock_handler.send_message.call_count == 2
            error_msg = mock_handler.send_message.call_args[0][0]
            assert 'An error occurred' in error_msg
            assert 'Unexpected error' in error_msg
