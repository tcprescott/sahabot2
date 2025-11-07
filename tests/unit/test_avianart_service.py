"""
Unit tests for Avianart randomizer service.

Tests the AvianartService class for generating door randomizer seeds.
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from application.services.randomizer.avianart_service import AvianartService
from application.services.randomizer.randomizer_service import RandomizerResult


class TestAvianartService:
    """Test suite for AvianartService."""

    @pytest.fixture
    def service(self):
        """Create an AvianartService instance."""
        return AvianartService()

    @pytest.fixture
    def mock_generate_response(self):
        """Mock response from initial generate API call."""
        return {
            'response': {
                'hash': 'test_hash_12345'
            }
        }

    @pytest.fixture
    def mock_permlink_response_finished(self):
        """Mock response from permlink API call when generation is finished."""
        return {
            'response': {
                'status': 'finished',
                'hash': 'test_hash_12345',
                'spoiler': {
                    'meta': {
                        'hash': 'Bow, Bombs, Hookshot, Mushroom, Lamp',
                        'version': '1.0.0'
                    }
                }
            }
        }

    @pytest.fixture
    def mock_permlink_response_generating(self):
        """Mock response from permlink API call when still generating."""
        return {
            'response': {
                'status': 'generating',
                'hash': 'test_hash_12345'
            }
        }

    @pytest.fixture
    def mock_permlink_response_failure(self):
        """Mock response from permlink API call when generation failed."""
        return {
            'response': {
                'status': 'failure',
                'message': 'Invalid preset configuration'
            }
        }

    @pytest.mark.asyncio
    async def test_generate_successful(
        self,
        service,
        mock_generate_response,
        mock_permlink_response_finished
    ):
        """Test successful seed generation."""
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client

            # Mock the post request (initial generation)
            mock_post_response = AsyncMock()
            mock_post_response.raise_for_status = MagicMock()
            mock_post_response.json = MagicMock(return_value=mock_generate_response)
            mock_client.post.return_value = mock_post_response

            # Mock the get request (polling for completion)
            mock_get_response = AsyncMock()
            mock_get_response.raise_for_status = MagicMock()
            mock_get_response.json = MagicMock(return_value=mock_permlink_response_finished)
            mock_client.get.return_value = mock_get_response

            result = await service.generate(preset='test-preset', race=True)

            # Verify result
            assert isinstance(result, RandomizerResult)
            assert result.randomizer == 'avianart'
            assert result.hash_id == 'test_hash_12345'
            assert result.url == 'https://avianart.games/perm/test_hash_12345'
            assert result.permalink == result.url
            assert result.settings == {'preset': 'test-preset', 'race': True}
            assert result.metadata['version'] == '1.0.0'
            assert result.metadata['preset'] == 'test-preset'
            assert 'file_select_code' in result.metadata

            # Verify API calls
            mock_client.post.assert_called_once()
            assert 'preset=test-preset' in mock_client.post.call_args[0][0]
            mock_client.get.assert_called_once()

    @pytest.mark.asyncio
    async def test_generate_without_preset_raises_error(self, service):
        """Test that generating without a preset raises ValueError."""
        with pytest.raises(ValueError, match="Preset name is required"):
            await service.generate(preset='', race=True)

    @pytest.mark.asyncio
    async def test_generate_with_failure_status(
        self,
        service,
        mock_generate_response,
        mock_permlink_response_failure
    ):
        """Test handling of failure status from API."""
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client

            # Mock the post request
            mock_post_response = AsyncMock()
            mock_post_response.raise_for_status = MagicMock()
            mock_post_response.json = MagicMock(return_value=mock_generate_response)
            mock_client.post.return_value = mock_post_response

            # Mock the get request to return failure
            mock_get_response = AsyncMock()
            mock_get_response.raise_for_status = MagicMock()
            mock_get_response.json = MagicMock(return_value=mock_permlink_response_failure)
            mock_client.get.return_value = mock_get_response

            with pytest.raises(ValueError, match="Failed to generate Avianart seed"):
                await service.generate(preset='test-preset', race=True)

    @pytest.mark.asyncio
    async def test_generate_timeout(
        self,
        service,
        mock_generate_response,
        mock_permlink_response_generating
    ):
        """Test timeout when seed generation takes too long."""
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client

            # Mock the post request
            mock_post_response = AsyncMock()
            mock_post_response.raise_for_status = MagicMock()
            mock_post_response.json = MagicMock(return_value=mock_generate_response)
            mock_client.post.return_value = mock_post_response

            # Mock the get request to always return 'generating' status
            mock_get_response = AsyncMock()
            mock_get_response.raise_for_status = MagicMock()
            mock_get_response.json = MagicMock(return_value=mock_permlink_response_generating)
            mock_client.get.return_value = mock_get_response

            # Patch sleep to avoid waiting in test
            with patch('asyncio.sleep', new=AsyncMock()):
                with pytest.raises(TimeoutError, match="Seed generation timed out"):
                    await service.generate(preset='test-preset', race=True)

    @pytest.mark.asyncio
    async def test_generate_race_false(
        self,
        service,
        mock_generate_response,
        mock_permlink_response_finished
    ):
        """Test generation with race=False."""
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client

            # Mock the post request
            mock_post_response = AsyncMock()
            mock_post_response.raise_for_status = MagicMock()
            mock_post_response.json = MagicMock(return_value=mock_generate_response)
            mock_client.post.return_value = mock_post_response

            # Mock the get request
            mock_get_response = AsyncMock()
            mock_get_response.raise_for_status = MagicMock()
            mock_get_response.json = MagicMock(return_value=mock_permlink_response_finished)
            mock_client.get.return_value = mock_get_response

            result = await service.generate(preset='test-preset', race=False)

            # Verify race setting was passed
            assert result.settings['race'] is False
            post_call_args = mock_client.post.call_args
            payload = post_call_args[1]['json']
            assert payload[0]['args']['race'] is False

    def test_extract_file_select_code_basic(self, service):
        """Test extraction of file select code."""
        result = {
            'response': {
                'spoiler': {
                    'meta': {
                        'hash': 'Bow, Bombs, Hookshot, Mushroom, Lamp'
                    }
                }
            }
        }

        code = service._extract_file_select_code(result)

        assert code == ['Bow', 'Bombs', 'Hookshot', 'Mushroom', 'Lamp']

    def test_extract_file_select_code_with_mapping(self, service):
        """Test extraction with code mapping."""
        result = {
            'response': {
                'spoiler': {
                    'meta': {
                        'hash': 'Bomb, Powder, Rod, Ocarina, Bug Net'
                    }
                }
            }
        }

        code = service._extract_file_select_code(result)

        # Should map Bomb->Bombs, Powder->Magic Powder, etc.
        assert code == ['Bombs', 'Magic Powder', 'Ice Rod', 'Flute', 'Bugnet']

    def test_extract_file_select_code_mixed(self, service):
        """Test extraction with mix of mapped and unmapped items."""
        result = {
            'response': {
                'spoiler': {
                    'meta': {
                        'hash': 'Bow, Bomb, Hookshot, Pearl, Key'
                    }
                }
            }
        }

        code = service._extract_file_select_code(result)

        # Should map Bomb->Bombs, Pearl->Moon Pearl, Key->Big Key
        assert code == ['Bow', 'Bombs', 'Hookshot', 'Moon Pearl', 'Big Key']
