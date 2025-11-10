"""
Test SMZ3 randomizer service and handlers.

This module tests the SMZ3 service and RaceTime handlers.
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from application.services.randomizer.smz3_service import SMZ3Service
from application.services.randomizer.randomizer_service import RandomizerResult
from racetime.smz3_race_handler import SMZ3RaceHandler


@pytest.mark.asyncio
async def test_smz3_service_generate():
    """Test basic SMZ3 seed generation."""
    service = SMZ3Service()

    settings = {
        "logic": "normal",
        "mode": "normal",
        "goal": "defeatBoth",
    }

    # Mock the httpx client
    with patch("httpx.AsyncClient") as mock_client:
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "slug": "test-slug-123",
            "guid": "test-guid-456",
        }
        mock_response.raise_for_status = MagicMock()

        mock_context = AsyncMock()
        mock_context.__aenter__.return_value.post = AsyncMock(
            return_value=mock_response
        )
        mock_client.return_value = mock_context

        result = await service.generate(
            settings=settings, tournament=True, spoilers=False
        )

        assert isinstance(result, RandomizerResult)
        assert result.randomizer == "smz3"
        assert "test-slug-123" in result.url
        assert result.hash_id == "test-slug-123"


@pytest.mark.asyncio
async def test_smz3_service_generate_with_spoiler():
    """Test SMZ3 seed generation with spoiler log."""
    service = SMZ3Service()

    settings = {
        "logic": "normal",
        "mode": "normal",
        "goal": "defeatBoth",
    }

    # Mock the httpx client
    with patch("httpx.AsyncClient") as mock_client:
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "slug": "test-slug-123",
            "guid": "test-guid-456",
        }
        mock_response.raise_for_status = MagicMock()

        mock_context = AsyncMock()
        mock_context.__aenter__.return_value.post = AsyncMock(
            return_value=mock_response
        )
        mock_client.return_value = mock_context

        result = await service.generate(
            settings=settings, tournament=False, spoilers=True, spoiler_key="test-key"
        )

        assert isinstance(result, RandomizerResult)
        assert result.spoiler_url is not None
        assert "test-key" in result.spoiler_url


@pytest.mark.asyncio
async def test_handle_smz3_race_default():
    """Test !race command with default settings."""
    # Create a mock handler with necessary methods
    handler = MagicMock()
    handler.send_message = AsyncMock()
    handler.data = {"status": {"value": "open"}, "goal": {"name": "Beat the games"}}

    # Bind the actual ex_race method to our mock
    handler.ex_race = SMZ3RaceHandler.ex_race.__get__(handler, SMZ3RaceHandler)

    # Mock the SMZ3 service
    with patch("racetime.smz3_race_handler.SMZ3Service") as mock_service_class:
        mock_service = MagicMock()
        mock_result = RandomizerResult(
            url="https://samus.link/seed/test-123",
            hash_id="test-123",
            settings={},
            randomizer="smz3",
        )
        mock_service.generate = AsyncMock(return_value=mock_result)
        mock_service_class.return_value = mock_service

        # Mock preset service
        with patch("racetime.smz3_race_handler.RandomizerPresetService"):
            # Call the handler method
            await handler.ex_race([], None)

            # Verify send_message was called with expected content
            handler.send_message.assert_called_once()
            sent_message = handler.send_message.call_args[0][0]
            assert "https://samus.link/seed/test-123" in sent_message
            assert "Beat the games" in sent_message


@pytest.mark.asyncio
async def test_handle_smz3_preset():
    """Test !preset command with specified preset."""
    # Create a mock handler with necessary methods
    handler = MagicMock()
    handler.send_message = AsyncMock()
    handler.data = {"status": {"value": "open"}, "goal": {"name": "Beat the games"}}

    # Bind the actual ex_preset method to our mock
    handler.ex_preset = SMZ3RaceHandler.ex_preset.__get__(handler, SMZ3RaceHandler)
    handler.ex_race = SMZ3RaceHandler.ex_race.__get__(handler, SMZ3RaceHandler)

    # Mock services
    with patch("racetime.smz3_race_handler.SMZ3Service") as mock_service_class, patch(
        "racetime.smz3_race_handler.RandomizerPresetService"
    ) as mock_preset_class:

        # Mock SMZ3 service
        mock_service = MagicMock()
        mock_result = RandomizerResult(
            url="https://samus.link/seed/test-456",
            hash_id="test-456",
            settings={"logic": "hard"},
            randomizer="smz3",
        )
        mock_service.generate = AsyncMock(return_value=mock_result)
        mock_service_class.return_value = mock_service

        # Mock preset service
        mock_preset_service = MagicMock()
        mock_preset = MagicMock()
        mock_preset.settings = {"logic": "hard", "mode": "normal"}
        mock_preset_service.get_preset_by_name = AsyncMock(return_value=mock_preset)
        mock_preset_class.return_value = mock_preset_service

        # Call the handler method
        await handler.ex_preset(["hard-mode"], None)

        # Verify send_message was called with expected content
        handler.send_message.assert_called_once()
        sent_message = handler.send_message.call_args[0][0]
        assert "https://samus.link/seed/test-456" in sent_message
        assert "Preset: hard-mode" in sent_message


@pytest.mark.asyncio
async def test_handle_smz3_spoiler():
    """Test !spoiler command."""
    # Create a mock handler with necessary methods
    handler = MagicMock()
    handler.send_message = AsyncMock()
    handler.data = {"status": {"value": "open"}, "goal": {"name": "Beat the games"}}

    # Bind the actual ex_spoiler method to our mock
    handler.ex_spoiler = SMZ3RaceHandler.ex_spoiler.__get__(handler, SMZ3RaceHandler)

    # Mock services
    with patch("racetime.smz3_race_handler.SMZ3Service") as mock_service_class, patch(
        "racetime.smz3_race_handler.RandomizerPresetService"
    ):

        # Mock SMZ3 service with spoiler
        mock_service = MagicMock()
        mock_result = RandomizerResult(
            url="https://samus.link/seed/test-789",
            hash_id="test-789",
            settings={},
            randomizer="smz3",
            spoiler_url="https://samus.link/api/spoiler/test-guid?key=spoiler",
        )
        mock_service.generate = AsyncMock(return_value=mock_result)
        mock_service_class.return_value = mock_service

        # Call the handler method
        await handler.ex_spoiler([], None)

        # Verify send_message was called with expected content
        handler.send_message.assert_called_once()
        sent_message = handler.send_message.call_args[0][0]
        assert "https://samus.link/seed/test-789" in sent_message
        assert "Spoiler" in sent_message
        assert "spoiler" in sent_message


@pytest.mark.asyncio
async def test_smz3_randomizer_service_integration():
    """Test that SMZ3 is registered with the main randomizer service."""
    from application.services.randomizer.randomizer_service import RandomizerService

    service = RandomizerService()

    # Check SMZ3 is in the list
    randomizers = service.list_randomizers()
    assert "smz3" in randomizers

    # Get SMZ3 service
    smz3_service = service.get_randomizer("smz3")
    assert isinstance(smz3_service, SMZ3Service)


if __name__ == "__main__":
    # Run with: python3 -m pytest tests/test_smz3.py -v
    pytest.main([__file__, "-v"])
