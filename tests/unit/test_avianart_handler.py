"""
Unit tests for Avianart RaceTime.gg command handler.

Tests the handle_avianart function that processes !avianart commands in race rooms.
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from racetime.command_handlers import handle_avianart
from application.services.randomizer.randomizer_service import RandomizerResult


class TestAvianartCommandHandler:
    """Test suite for Avianart command handler."""

    @pytest.fixture
    def mock_command(self):
        """Mock RacetimeChatCommand."""
        command = MagicMock()
        command.command = 'avianart'
        return command

    @pytest.fixture
    def mock_race_data(self):
        """Mock race data."""
        return {
            'status': {'value': 'open'},
            'goal': {'name': 'Test Race'},
            'entrants': []
        }

    @pytest.fixture
    def mock_user(self):
        """Mock user."""
        user = MagicMock()
        user.id = 123
        user.discord_username = 'TestUser'
        return user

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
    async def test_handle_avianart_success(
        self,
        mock_command,
        mock_race_data,
        mock_user,
        mock_result
    ):
        """Test successful Avianart seed generation."""
        with patch('application.services.randomizer.avianart_service.AvianartService') as mock_service_class:
            mock_service = AsyncMock()
            mock_service.generate.return_value = mock_result
            mock_service_class.return_value = mock_service

            response = await handle_avianart(
                _command=mock_command,
                _args=['test-preset'],
                _racetime_user_id='test_user_123',
                _race_data=mock_race_data,
                _user=mock_user
            )

            # Verify service was called correctly
            mock_service.generate.assert_called_once_with(
                preset='test-preset',
                race=True
            )

            # Verify response includes URL and code
            assert 'https://avianart.games/perm/test_hash' in response
            assert 'Bow/Bombs/Hookshot/Mushroom/Lamp' in response
            assert '1.0.0' in response

    @pytest.mark.asyncio
    async def test_handle_avianart_no_args(
        self,
        mock_command,
        mock_race_data,
        mock_user
    ):
        """Test !avianart without preset name."""
        response = await handle_avianart(
            _command=mock_command,
            _args=[],
            _racetime_user_id='test_user_123',
            _race_data=mock_race_data,
            _user=mock_user
        )

        assert 'Usage: !avianart <preset_name>' in response

    @pytest.mark.asyncio
    async def test_handle_avianart_value_error(
        self,
        mock_command,
        mock_race_data,
        mock_user
    ):
        """Test handling of ValueError (invalid preset)."""
        with patch('application.services.randomizer.avianart_service.AvianartService') as mock_service_class:
            mock_service = AsyncMock()
            mock_service.generate.side_effect = ValueError("Invalid preset configuration")
            mock_service_class.return_value = mock_service

            response = await handle_avianart(
                _command=mock_command,
                _args=['invalid-preset'],
                _racetime_user_id='test_user_123',
                _race_data=mock_race_data,
                _user=mock_user
            )

            assert 'Error: Invalid preset configuration' in response

    @pytest.mark.asyncio
    async def test_handle_avianart_timeout(
        self,
        mock_command,
        mock_race_data,
        mock_user
    ):
        """Test handling of TimeoutError."""
        with patch('application.services.randomizer.avianart_service.AvianartService') as mock_service_class:
            mock_service = AsyncMock()
            mock_service.generate.side_effect = TimeoutError("Generation timed out")
            mock_service_class.return_value = mock_service

            response = await handle_avianart(
                _command=mock_command,
                _args=['test-preset'],
                _racetime_user_id='test_user_123',
                _race_data=mock_race_data,
                _user=mock_user
            )

            assert 'Seed generation timed out' in response

    @pytest.mark.asyncio
    async def test_handle_avianart_generic_exception(
        self,
        mock_command,
        mock_race_data,
        mock_user
    ):
        """Test handling of generic exceptions."""
        with patch('application.services.randomizer.avianart_service.AvianartService') as mock_service_class:
            mock_service = AsyncMock()
            mock_service.generate.side_effect = Exception("Unexpected error")
            mock_service_class.return_value = mock_service

            response = await handle_avianart(
                _command=mock_command,
                _args=['test-preset'],
                _racetime_user_id='test_user_123',
                _race_data=mock_race_data,
                _user=mock_user
            )

            assert 'An error occurred' in response
            assert 'Unexpected error' in response

    @pytest.mark.asyncio
    async def test_handle_avianart_without_user(
        self,
        mock_command,
        mock_race_data,
        mock_result
    ):
        """Test !avianart command without authenticated user."""
        with patch('application.services.randomizer.avianart_service.AvianartService') as mock_service_class:
            mock_service = AsyncMock()
            mock_service.generate.return_value = mock_result
            mock_service_class.return_value = mock_service

            # Should still work without user (unlike !mystery which requires auth)
            response = await handle_avianart(
                _command=mock_command,
                _args=['test-preset'],
                _racetime_user_id='test_user_123',
                _race_data=mock_race_data,
                _user=None
            )

            assert 'https://avianart.games/perm/test_hash' in response
