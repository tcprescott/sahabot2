"""
Unit tests for Super Metroid randomizer service.

Tests the SM service methods for VARIA, DASH, and multiworld seed generation.
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from application.services.randomizer.sm_service import SMService
from application.services.randomizer.randomizer_service import RandomizerResult


@pytest.fixture
def sm_service():
    """Create an SM service instance."""
    return SMService()


class TestSMService:
    """Test cases for SM service."""

    @pytest.mark.asyncio
    async def test_generate_varia_basic(self, sm_service):
        """Test basic VARIA seed generation."""
        settings = {
            'logic': 'casual',
            'itemProgression': 'normal',
        }

        mock_response = MagicMock()
        mock_response.json.return_value = {
            'slug': 'test-slug-123',
            'guid': 'guid-456',
        }
        mock_response.raise_for_status = MagicMock()

        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                return_value=mock_response
            )

            result = await sm_service.generate_varia(
                settings=settings,
                tournament=True,
                spoilers=False
            )

        assert isinstance(result, RandomizerResult)
        assert result.randomizer == 'sm-varia'
        assert result.hash_id == 'test-slug-123'
        assert 'test-slug-123' in result.url
        assert result.metadata['type'] == 'varia'

    @pytest.mark.asyncio
    async def test_generate_varia_with_spoilers(self, sm_service):
        """Test VARIA seed generation with spoiler log."""
        settings = {
            'logic': 'master',
        }

        mock_response = MagicMock()
        mock_response.json.return_value = {
            'slug': 'test-slug-789',
            'guid': 'guid-abc',
        }
        mock_response.raise_for_status = MagicMock()

        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                return_value=mock_response
            )

            result = await sm_service.generate_varia(
                settings=settings,
                tournament=True,
                spoilers=True,
                spoiler_key='secret123'
            )

        assert result.spoiler_url is not None
        assert 'guid-abc' in result.spoiler_url
        assert 'secret123' in result.spoiler_url

    @pytest.mark.asyncio
    async def test_generate_varia_race_mode(self, sm_service):
        """Test VARIA seed with race mode enabled."""
        settings = {'logic': 'casual'}

        mock_response = MagicMock()
        mock_response.json.return_value = {
            'slug': 'race-slug',
            'guid': 'race-guid',
        }
        mock_response.raise_for_status = MagicMock()

        with patch('httpx.AsyncClient') as mock_client:
            mock_post = AsyncMock(return_value=mock_response)
            mock_client.return_value.__aenter__.return_value.post = mock_post

            await sm_service.generate_varia(
                settings=settings,
                tournament=True
            )

            # Verify race mode was set
            call_args = mock_post.call_args
            posted_json = call_args[1]['json']
            assert posted_json['race'] == 'true'

    @pytest.mark.asyncio
    async def test_generate_dash_basic(self, sm_service):
        """Test basic DASH seed generation."""
        settings = {
            'area_rando': False,
            'major_minor_split': True,
        }

        mock_response = MagicMock()
        mock_response.json.return_value = {
            'id': 'dash-123',
            'seed': 'dash-seed-456',
            'hash': 'hash-789',
        }
        mock_response.raise_for_status = MagicMock()

        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                return_value=mock_response
            )

            result = await sm_service.generate_dash(
                settings=settings,
                tournament=True,
                spoilers=False
            )

        assert isinstance(result, RandomizerResult)
        assert result.randomizer == 'sm-dash'
        assert result.hash_id == 'hash-789'
        assert 'dash-123' in result.url
        assert result.metadata['type'] == 'dash'

    @pytest.mark.asyncio
    async def test_generate_dash_with_area_rando(self, sm_service):
        """Test DASH seed with area randomization."""
        settings = {
            'area_rando': True,
            'major_minor_split': True,
        }

        mock_response = MagicMock()
        mock_response.json.return_value = {
            'id': 'dash-area-123',
            'hash': 'hash-area',
        }
        mock_response.raise_for_status = MagicMock()

        with patch('httpx.AsyncClient') as mock_client:
            mock_post = AsyncMock(return_value=mock_response)
            mock_client.return_value.__aenter__.return_value.post = mock_post

            result = await sm_service.generate_dash(
                settings=settings,
                tournament=False
            )

        assert result.randomizer == 'sm-dash'
        # Verify settings were passed through
        call_args = mock_post.call_args
        posted_json = call_args[1]['json']
        assert posted_json['area_rando'] is True

    @pytest.mark.asyncio
    async def test_generate_total_randomization(self, sm_service):
        """Test total randomization seed generation."""
        settings = {'preset': 'total'}

        mock_response = MagicMock()
        mock_response.json.return_value = {
            'id': 'total-123',
            'hash': 'hash-total',
        }
        mock_response.raise_for_status = MagicMock()

        with patch('httpx.AsyncClient') as mock_client:
            mock_post = AsyncMock(return_value=mock_response)
            mock_client.return_value.__aenter__.return_value.post = mock_post

            result = await sm_service.generate(
                settings=settings,
                randomizer_type='total',
                tournament=True
            )

        assert result.randomizer == 'sm-dash'
        # Verify total randomization settings
        call_args = mock_post.call_args
        posted_json = call_args[1]['json']
        assert posted_json['area_rando'] is True
        assert posted_json['major_minor_split'] is True
        assert posted_json['boss_rando'] is True

    @pytest.mark.asyncio
    async def test_generate_multiworld(self, sm_service):
        """Test multiworld seed generation."""
        settings = {
            'player_count': 2,
        }

        mock_response = MagicMock()
        mock_response.json.return_value = {
            'slug': 'multiworld-123',
            'guid': 'mw-guid',
        }
        mock_response.raise_for_status = MagicMock()

        with patch('httpx.AsyncClient') as mock_client:
            mock_post = AsyncMock(return_value=mock_response)
            mock_client.return_value.__aenter__.return_value.post = mock_post

            result = await sm_service.generate(
                settings=settings,
                randomizer_type='multiworld',
                tournament=True
            )

        assert result.randomizer == 'sm-varia'
        # Verify multiworld settings
        call_args = mock_post.call_args
        posted_json = call_args[1]['json']
        assert posted_json['multiworld'] is True

    @pytest.mark.asyncio
    async def test_generate_varia_route(self, sm_service):
        """Test that 'varia' type routes to generate_varia."""
        settings = {'logic': 'expert'}

        mock_response = MagicMock()
        mock_response.json.return_value = {
            'slug': 'varia-route',
            'guid': 'guid-route',
        }
        mock_response.raise_for_status = MagicMock()

        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                return_value=mock_response
            )

            result = await sm_service.generate(
                settings=settings,
                randomizer_type='varia',
                tournament=False
            )

        assert result.randomizer == 'sm-varia'
        assert 'varia-route' in result.url

    @pytest.mark.asyncio
    async def test_generate_dash_route(self, sm_service):
        """Test that 'dash' type routes to generate_dash."""
        settings = {'major_minor_split': True}

        mock_response = MagicMock()
        mock_response.json.return_value = {
            'id': 'dash-route',
            'hash': 'hash-route',
        }
        mock_response.raise_for_status = MagicMock()

        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                return_value=mock_response
            )

            result = await sm_service.generate(
                settings=settings,
                randomizer_type='dash',
                tournament=False
            )

        assert result.randomizer == 'sm-dash'
        assert 'dash-route' in result.url

    @pytest.mark.asyncio
    async def test_generate_invalid_type(self, sm_service):
        """Test that invalid randomizer type raises ValueError."""
        settings = {}

        with pytest.raises(ValueError, match="Unknown SM randomizer type"):
            await sm_service.generate(
                settings=settings,
                randomizer_type='invalid',
                tournament=True
            )

    @pytest.mark.asyncio
    async def test_varia_url_construction(self, sm_service):
        """Test VARIA URL is constructed correctly."""
        settings = {}

        mock_response = MagicMock()
        mock_response.json.return_value = {
            'slug': 'url-test-123',
            'guid': 'guid-test',
        }
        mock_response.raise_for_status = MagicMock()

        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                return_value=mock_response
            )

            result = await sm_service.generate_varia(settings)

        assert result.url == f"{sm_service.varia_baseurl}/seed/url-test-123"
        assert result.permalink == result.url

    @pytest.mark.asyncio
    async def test_dash_url_construction(self, sm_service):
        """Test DASH URL is constructed correctly."""
        settings = {}

        mock_response = MagicMock()
        mock_response.json.return_value = {
            'id': 'url-test-456',
            'hash': 'hash-test',
        }
        mock_response.raise_for_status = MagicMock()

        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                return_value=mock_response
            )

            result = await sm_service.generate_dash(settings)

        assert result.url == f"{sm_service.dash_baseurl}/seed/url-test-456"
        assert result.permalink == result.url

    @pytest.mark.asyncio
    async def test_metadata_includes_all_fields(self, sm_service):
        """Test that metadata includes all response fields."""
        settings = {}

        mock_response = MagicMock()
        mock_response.json.return_value = {
            'slug': 'meta-test',
            'guid': 'meta-guid',
            'extra_field': 'extra_value',
            'another_field': 123,
        }
        mock_response.raise_for_status = MagicMock()

        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                return_value=mock_response
            )

            result = await sm_service.generate_varia(settings)

        assert result.metadata['extra_field'] == 'extra_value'
        assert result.metadata['another_field'] == 123
        assert result.metadata['type'] == 'varia'
