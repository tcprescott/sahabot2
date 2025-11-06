"""
Test SMZ3 randomizer service and handlers.

This module tests the SMZ3 service and RaceTime handlers.
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from application.services.randomizer.smz3_service import SMZ3Service
from application.services.randomizer.randomizer_service import RandomizerResult
from racetime.smz3_handler import (
    handle_smz3_race,
    handle_smz3_preset,
    handle_smz3_spoiler,
)
from models import RacetimeChatCommand, CommandResponseType, CommandScope


@pytest.mark.asyncio
async def test_smz3_service_generate():
    """Test basic SMZ3 seed generation."""
    service = SMZ3Service()
    
    settings = {
        'logic': 'normal',
        'mode': 'normal',
        'goal': 'defeatBoth',
    }
    
    # Mock the httpx client
    with patch('httpx.AsyncClient') as mock_client:
        mock_response = MagicMock()
        mock_response.json.return_value = {
            'slug': 'test-slug-123',
            'guid': 'test-guid-456',
        }
        mock_response.raise_for_status = MagicMock()
        
        mock_context = AsyncMock()
        mock_context.__aenter__.return_value.post = AsyncMock(return_value=mock_response)
        mock_client.return_value = mock_context
        
        result = await service.generate(
            settings=settings,
            tournament=True,
            spoilers=False
        )
        
        assert isinstance(result, RandomizerResult)
        assert result.randomizer == 'smz3'
        assert 'test-slug-123' in result.url
        assert result.hash_id == 'test-slug-123'


@pytest.mark.asyncio
async def test_smz3_service_generate_with_spoiler():
    """Test SMZ3 seed generation with spoiler log."""
    service = SMZ3Service()
    
    settings = {
        'logic': 'normal',
        'mode': 'normal',
        'goal': 'defeatBoth',
    }
    
    # Mock the httpx client
    with patch('httpx.AsyncClient') as mock_client:
        mock_response = MagicMock()
        mock_response.json.return_value = {
            'slug': 'test-slug-123',
            'guid': 'test-guid-456',
        }
        mock_response.raise_for_status = MagicMock()
        
        mock_context = AsyncMock()
        mock_context.__aenter__.return_value.post = AsyncMock(return_value=mock_response)
        mock_client.return_value = mock_context
        
        result = await service.generate(
            settings=settings,
            tournament=False,
            spoilers=True,
            spoiler_key='test-key'
        )
        
        assert isinstance(result, RandomizerResult)
        assert result.spoiler_url is not None
        assert 'test-key' in result.spoiler_url


@pytest.mark.asyncio
async def test_handle_smz3_race_default():
    """Test !race command with default settings."""
    command = RacetimeChatCommand()
    command.command = 'race'
    
    race_data = {
        'goal': {'name': 'Beat the games'}
    }
    
    # Mock the SMZ3 service
    with patch('racetime.smz3_handler.SMZ3Service') as mock_service_class:
        mock_service = MagicMock()
        mock_result = RandomizerResult(
            url='https://samus.link/seed/test-123',
            hash_id='test-123',
            settings={},
            randomizer='smz3',
        )
        mock_service.generate = AsyncMock(return_value=mock_result)
        mock_service_class.return_value = mock_service
        
        # Mock preset service
        with patch('racetime.smz3_handler.RandomizerPresetService'):
            response = await handle_smz3_race(
                command,
                [],  # No args (default settings)
                'test-user-id',
                race_data,
                None
            )
            
            assert 'https://samus.link/seed/test-123' in response
            assert 'Beat the games' in response


@pytest.mark.asyncio
async def test_handle_smz3_preset():
    """Test !preset command with specified preset."""
    command = RacetimeChatCommand()
    command.command = 'preset'
    
    race_data = {
        'goal': {'name': 'Beat the games'}
    }
    
    # Mock services
    with patch('racetime.smz3_handler.SMZ3Service') as mock_service_class, \
         patch('racetime.smz3_handler.RandomizerPresetService') as mock_preset_class:
        
        # Mock SMZ3 service
        mock_service = MagicMock()
        mock_result = RandomizerResult(
            url='https://samus.link/seed/test-456',
            hash_id='test-456',
            settings={'logic': 'hard'},
            randomizer='smz3',
        )
        mock_service.generate = AsyncMock(return_value=mock_result)
        mock_service_class.return_value = mock_service
        
        # Mock preset service
        mock_preset_service = MagicMock()
        mock_preset = MagicMock()
        mock_preset.settings = {'logic': 'hard', 'mode': 'normal'}
        mock_preset_service.get_preset_by_name = AsyncMock(return_value=mock_preset)
        mock_preset_class.return_value = mock_preset_service
        
        response = await handle_smz3_preset(
            command,
            ['hard-mode'],  # Preset name
            'test-user-id',
            race_data,
            None
        )
        
        assert 'https://samus.link/seed/test-456' in response
        assert 'Preset: hard-mode' in response


@pytest.mark.asyncio
async def test_handle_smz3_spoiler():
    """Test !spoiler command."""
    command = RacetimeChatCommand()
    command.command = 'spoiler'
    
    race_data = {
        'goal': {'name': 'Beat the games'}
    }
    
    # Mock services
    with patch('racetime.smz3_handler.SMZ3Service') as mock_service_class, \
         patch('racetime.smz3_handler.RandomizerPresetService'):
        
        # Mock SMZ3 service with spoiler
        mock_service = MagicMock()
        mock_result = RandomizerResult(
            url='https://samus.link/seed/test-789',
            hash_id='test-789',
            settings={},
            randomizer='smz3',
            spoiler_url='https://samus.link/api/spoiler/test-guid?key=spoiler'
        )
        mock_service.generate = AsyncMock(return_value=mock_result)
        mock_service_class.return_value = mock_service
        
        response = await handle_smz3_spoiler(
            command,
            [],  # No args
            'test-user-id',
            race_data,
            None
        )
        
        assert 'https://samus.link/seed/test-789' in response
        assert 'Spoiler:' in response
        assert 'spoiler' in response


@pytest.mark.asyncio
async def test_smz3_randomizer_service_integration():
    """Test that SMZ3 is registered with the main randomizer service."""
    from application.services.randomizer.randomizer_service import RandomizerService
    
    service = RandomizerService()
    
    # Check SMZ3 is in the list
    randomizers = service.list_randomizers()
    assert 'smz3' in randomizers
    
    # Get SMZ3 service
    smz3_service = service.get_randomizer('smz3')
    assert isinstance(smz3_service, SMZ3Service)


if __name__ == '__main__':
    # Run with: python3 -m pytest tests/test_smz3.py -v
    pytest.main([__file__, '-v'])
