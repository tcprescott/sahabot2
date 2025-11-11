"""
Tests for MatchRaceMixin and combined handler classes.

Tests that MatchRaceMixin can be combined with category-specific handlers
to provide both match processing and category-specific commands.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from racetime.match_race_handler import create_match_handler_class
from racetime.alttpr_handler import ALTTPRRaceHandler
from racetime.sm_race_handler import SMRaceHandler
from racetime.smz3_race_handler import SMZ3RaceHandler
from racetime.client import SahaRaceHandler


class TestMatchRaceMixin:
    """Test MatchRaceMixin functionality."""

    def test_create_match_handler_class_with_alttpr(self):
        """Test creating a match handler class combined with ALTTPRRaceHandler."""
        MatchALTTPRRaceHandler = create_match_handler_class(ALTTPRRaceHandler)

        # Verify class name
        assert MatchALTTPRRaceHandler.__name__ == "MatchALTTPRRaceHandler"

        # Verify MRO includes both mixin and base handler
        mro_names = [c.__name__ for c in MatchALTTPRRaceHandler.__mro__]
        assert "MatchRaceMixin" in mro_names
        assert "ALTTPRRaceHandler" in mro_names
        assert "SahaRaceHandler" in mro_names

        # Verify mixin comes before base handler (for correct method resolution)
        mixin_index = mro_names.index("MatchRaceMixin")
        alttpr_index = mro_names.index("ALTTPRRaceHandler")
        assert mixin_index < alttpr_index

    def test_create_match_handler_class_with_sm(self):
        """Test creating a match handler class combined with SMRaceHandler."""
        MatchSMRaceHandler = create_match_handler_class(SMRaceHandler)

        assert MatchSMRaceHandler.__name__ == "MatchSMRaceHandler"

        mro_names = [c.__name__ for c in MatchSMRaceHandler.__mro__]
        assert "MatchRaceMixin" in mro_names
        assert "SMRaceHandler" in mro_names

    def test_create_match_handler_class_with_smz3(self):
        """Test creating a match handler class combined with SMZ3RaceHandler."""
        MatchSMZ3RaceHandler = create_match_handler_class(SMZ3RaceHandler)

        assert MatchSMZ3RaceHandler.__name__ == "MatchSMZ3RaceHandler"

        mro_names = [c.__name__ for c in MatchSMZ3RaceHandler.__mro__]
        assert "MatchRaceMixin" in mro_names
        assert "SMZ3RaceHandler" in mro_names

    def test_create_match_handler_class_with_base(self):
        """Test creating a match handler class combined with base SahaRaceHandler."""
        MatchSahaRaceHandler = create_match_handler_class(SahaRaceHandler)

        assert MatchSahaRaceHandler.__name__ == "MatchSahaRaceHandler"

        mro_names = [c.__name__ for c in MatchSahaRaceHandler.__mro__]
        assert "MatchRaceMixin" in mro_names
        assert "SahaRaceHandler" in mro_names

    @pytest.mark.asyncio
    async def test_match_handler_has_alttpr_commands(self):
        """Test that combined handler has ALTTPR-specific commands."""
        MatchALTTPRRaceHandler = create_match_handler_class(ALTTPRRaceHandler)

        # Verify ALTTPR commands are available
        assert hasattr(MatchALTTPRRaceHandler, "ex_mystery")
        assert hasattr(MatchALTTPRRaceHandler, "ex_vt")
        assert hasattr(MatchALTTPRRaceHandler, "ex_vtspoiler")
        assert hasattr(MatchALTTPRRaceHandler, "ex_avianart")
        assert hasattr(MatchALTTPRRaceHandler, "ex_custommystery")

    @pytest.mark.asyncio
    async def test_match_handler_has_sm_commands(self):
        """Test that combined handler has SM-specific commands."""
        MatchSMRaceHandler = create_match_handler_class(SMRaceHandler)

        # Verify SM commands are available
        assert hasattr(MatchSMRaceHandler, "ex_varia")
        assert hasattr(MatchSMRaceHandler, "ex_dash")
        assert hasattr(MatchSMRaceHandler, "ex_total")
        assert hasattr(MatchSMRaceHandler, "ex_multiworld")

    @pytest.mark.asyncio
    async def test_match_handler_has_smz3_commands(self):
        """Test that combined handler has SMZ3-specific commands."""
        MatchSMZ3RaceHandler = create_match_handler_class(SMZ3RaceHandler)

        # Verify SMZ3 commands are available
        assert hasattr(MatchSMZ3RaceHandler, "ex_race")
        assert hasattr(MatchSMZ3RaceHandler, "ex_preset")
        assert hasattr(MatchSMZ3RaceHandler, "ex_spoiler")

    @pytest.mark.asyncio
    async def test_match_handler_has_base_commands(self):
        """Test that combined handler has base SahaRaceHandler commands."""
        MatchSahaRaceHandler = create_match_handler_class(SahaRaceHandler)

        # Verify base commands are available
        assert hasattr(MatchSahaRaceHandler, "ex_test")
        assert hasattr(MatchSahaRaceHandler, "ex_help")
        assert hasattr(MatchSahaRaceHandler, "ex_status")
        assert hasattr(MatchSahaRaceHandler, "ex_race")
        assert hasattr(MatchSahaRaceHandler, "ex_time")
        assert hasattr(MatchSahaRaceHandler, "ex_entrants")

    @pytest.mark.asyncio
    async def test_match_handler_processes_race_finish(self):
        """Test that match handler processes race finish events."""
        MatchALTTPRRaceHandler = create_match_handler_class(ALTTPRRaceHandler)

        # Create mock handler instance
        mock_bot = MagicMock()

        # Mock the parent class __init__ to avoid websocket setup
        with patch.object(SahaRaceHandler, "__init__", return_value=None):
            handler = MatchALTTPRRaceHandler(
                bot_instance=mock_bot,
                match_id=123,
            )

        # Manually set up handler attributes that would normally be set by __init__
        handler.bot = mock_bot
        handler.data = {
            "name": "alttpr/test-room-1234",
            "status": {"value": "in_progress"},
            "entrants": [],
        }
        handler._race_finished = False
        handler._previous_entrant_statuses = {}
        handler._previous_entrant_ids = set()
        handler._first_data_update = True
        handler._bot_created_room = False
        handler._user_repository = MagicMock()

        # Verify match_id is set
        assert handler.match_id == 123

        # Mock the race_data method to test race finish processing
        with patch(
            "application.services.tournaments.tournament_service.TournamentService.process_match_race_finish"
        ) as mock_process:
            mock_process.return_value = AsyncMock()

            # Simulate race finishing
            race_data = {
                "race": {
                    "name": "alttpr/test-room-1234",
                    "status": {"value": "finished"},
                    "entrants": [
                        {
                            "user": {"id": "user1"},
                            "status": {"value": "done"},
                            "finish_time": "PT1H23M45S",
                            "place": 1,
                        }
                    ],
                }
            }

            # Call race_data to trigger processing
            await handler.race_data(race_data)

            # Verify match finish was processed
            assert handler._race_finished is True
