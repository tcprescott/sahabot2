"""
Tests for automatic match handler selection when joining race rooms.

Verifies that:
1. join_race_room() detects if a room is for a match
2. Match handlers are used for match rooms
3. Base handlers are used for non-match rooms
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from racetime.client import RacetimeBot


class TestMatchHandlerSelection:
    """Test automatic match handler selection in join_race_room."""

    @pytest.mark.asyncio
    async def test_join_race_room_uses_match_handler_for_match_room(self):
        """Test that join_race_room uses match handler when room is for a match."""
        # Mock the Bot.__init__ to avoid actual connection
        with patch("racetime.client.Bot.__init__", return_value=None):
            # Create mock bot
            bot = RacetimeBot(
                category_slug="alttpr",
                client_id="test_client",
                client_secret="test_secret",
                bot_id=1,
                handler_class_name="ALTTPRRaceHandler",
            )
            bot.category_slug = "alttpr"

            # Mock HTTP session
            bot.http = MagicMock()

            # Mock race data fetch
            mock_race_data = {
                "name": "alttpr/test-room-1234",
                "status": {"value": "open"},
                "category": {"slug": "alttpr"},
                "entrants": [],
                "websocket_bot_url": "wss://example.com/ws",
            }

            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json = AsyncMock(return_value=mock_race_data)
            mock_response.raise_for_status = MagicMock()

            mock_get = AsyncMock(return_value=mock_response)
            mock_get.__aenter__ = AsyncMock(return_value=mock_response)
            mock_get.__aexit__ = AsyncMock(return_value=None)

            bot.http.get = MagicMock(return_value=mock_get)

            # Mock _get_match_id_for_room to return a match ID
            with patch.object(bot, "_get_match_id_for_room", return_value=AsyncMock(return_value=42)):
                # Mock create_match_handler to verify it's called
                mock_match_handler = MagicMock()
                mock_match_handler._bot_created_room = False
                with patch.object(
                    bot, "create_match_handler", return_value=mock_match_handler
                ) as mock_create_match:
                    # Mock create_handler to verify it's NOT called
                    with patch.object(bot, "create_handler") as mock_create_base:
                        handler = await bot.join_race_room("alttpr/test-room-1234", force=True)

                        # Verify match handler was created
                        mock_create_match.assert_called_once()
                        # Verify base handler was NOT created
                        mock_create_base.assert_not_called()
                        # Verify handler was returned
                        assert handler == mock_match_handler

    @pytest.mark.asyncio
    async def test_join_race_room_uses_base_handler_for_non_match_room(self):
        """Test that join_race_room uses base handler when room is not for a match."""
        # Mock the Bot.__init__ to avoid actual connection
        with patch("racetime.client.Bot.__init__", return_value=None):
            # Create mock bot
            bot = RacetimeBot(
                category_slug="alttpr",
                client_id="test_client",
                client_secret="test_secret",
                bot_id=1,
                handler_class_name="ALTTPRRaceHandler",
            )
            bot.category_slug = "alttpr"

            # Mock HTTP session
            bot.http = MagicMock()

            # Mock race data fetch
            mock_race_data = {
                "name": "alttpr/test-room-1234",
                "status": {"value": "open"},
                "category": {"slug": "alttpr"},
                "entrants": [],
                "websocket_bot_url": "wss://example.com/ws",
            }

            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json = AsyncMock(return_value=mock_race_data)
            mock_response.raise_for_status = MagicMock()

            mock_get = AsyncMock(return_value=mock_response)
            mock_get.__aenter__ = AsyncMock(return_value=mock_response)
            mock_get.__aexit__ = AsyncMock(return_value=None)

            bot.http.get = MagicMock(return_value=mock_get)

            # Mock _get_match_id_for_room to return None (no match)
            with patch.object(bot, "_get_match_id_for_room", return_value=AsyncMock(return_value=None)):
                # Mock create_handler to verify it's called
                mock_base_handler = MagicMock()
                mock_base_handler._bot_created_room = False
                with patch.object(
                    bot, "create_handler", return_value=mock_base_handler
                ) as mock_create_base:
                    # Mock create_match_handler to verify it's NOT called
                    with patch.object(bot, "create_match_handler") as mock_create_match:
                        handler = await bot.join_race_room("alttpr/test-room-1234", force=True)

                        # Verify base handler was created
                        mock_create_base.assert_called_once()
                        # Verify match handler was NOT called
                        mock_create_match.assert_not_called()
                        # Verify handler was returned
                        assert handler == mock_base_handler

    @pytest.mark.asyncio
    async def test_get_match_id_for_room_returns_match_id(self):
        """Test that _get_match_id_for_room returns match ID when room is linked."""
        with patch("racetime.client.Bot.__init__", return_value=None):
            bot = RacetimeBot(
                category_slug="alttpr",
                client_id="test_client",
                client_secret="test_secret",
            )

            # Mock RacetimeRoom.filter to return a room with match_id
            mock_room = MagicMock()
            mock_room.match_id = 42

            with patch("racetime.client.RacetimeRoom") as mock_room_model:
                mock_filter = MagicMock()
                mock_filter.first = AsyncMock(return_value=mock_room)
                mock_room_model.filter = MagicMock(return_value=mock_filter)

                match_id = await bot._get_match_id_for_room("alttpr/test-room-1234")

                assert match_id == 42
                mock_room_model.filter.assert_called_once_with(slug="alttpr/test-room-1234")

    @pytest.mark.asyncio
    async def test_get_match_id_for_room_returns_none_when_no_match(self):
        """Test that _get_match_id_for_room returns None when room has no match."""
        with patch("racetime.client.Bot.__init__", return_value=None):
            bot = RacetimeBot(
                category_slug="alttpr",
                client_id="test_client",
                client_secret="test_secret",
            )

            # Mock RacetimeRoom.filter to return a room without match_id
            mock_room = MagicMock()
            mock_room.match_id = None

            with patch("racetime.client.RacetimeRoom") as mock_room_model:
                mock_filter = MagicMock()
                mock_filter.first = AsyncMock(return_value=mock_room)
                mock_room_model.filter = MagicMock(return_value=mock_filter)

                match_id = await bot._get_match_id_for_room("alttpr/test-room-1234")

                assert match_id is None

    @pytest.mark.asyncio
    async def test_get_match_id_for_room_returns_none_when_no_room(self):
        """Test that _get_match_id_for_room returns None when room doesn't exist."""
        with patch("racetime.client.Bot.__init__", return_value=None):
            bot = RacetimeBot(
                category_slug="alttpr",
                client_id="test_client",
                client_secret="test_secret",
            )

            # Mock RacetimeRoom.filter to return None
            with patch("racetime.client.RacetimeRoom") as mock_room_model:
                mock_filter = MagicMock()
                mock_filter.first = AsyncMock(return_value=None)
                mock_room_model.filter = MagicMock(return_value=mock_filter)

                match_id = await bot._get_match_id_for_room("alttpr/test-room-1234")

                assert match_id is None
