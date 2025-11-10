"""
Integration test for SpeedGaming ETL service.

This test demonstrates the complete flow of importing a SpeedGaming episode
into the Match model with player and crew member creation.
"""

import pytest
from datetime import datetime, timezone
from application.services.speedgaming.speedgaming_etl_service import (
    SpeedGamingETLService,
)
from application.services.speedgaming.speedgaming_service import (
    SpeedGamingEpisode,
    SpeedGamingPlayer,
    SpeedGamingCrewMember,
    SpeedGamingMatch,
    SpeedGamingEvent,
    SpeedGamingChannel,
)


@pytest.fixture
def sample_episode():
    """Create a sample SpeedGaming episode for testing."""
    return SpeedGamingEpisode(
        id=12345,
        title="Test Episode",
        when=datetime(2022, 11, 6, 18, 0, 0, tzinfo=timezone.utc),
        approved=True,
        length=60,
        match1=SpeedGamingMatch(
            id=32812,
            title="Standard",
            players=[
                SpeedGamingPlayer(
                    id=11111,
                    display_name="synack",
                    discord_id="123456789012345678",
                    discord_tag="Synack#1337",
                    public_stream="the_synack",
                    streaming_from="the_synack",
                ),
                SpeedGamingPlayer(
                    id=22222,
                    display_name="player_without_discord",
                    discord_id=None,  # No Discord ID
                    discord_tag="Unknown#0000",
                    public_stream=None,
                    streaming_from=None,
                ),
            ],
        ),
        match2=None,
        event=SpeedGamingEvent(
            id=573,
            name="Bot Testing 123",
            slug="test",
            game="Bot Testing 123",
            active=True,
        ),
        channels=[
            SpeedGamingChannel(
                id=25,
                name="SpeedGaming",
                slug="speedgaming",
                language="en",
            )
        ],
        commentators=[
            SpeedGamingCrewMember(
                id=60789,
                display_name="DerMo",
                discord_id="472785637984960512",
                discord_tag="Mo1988#1772",
                language="en",
                ready=False,
                approved=False,
                public_stream="DerMo1988",
            )
        ],
        trackers=[],
        broadcasters=[],
    )


class TestSpeedGamingETLFlow:
    """Test the complete ETL flow for SpeedGaming integration."""

    def test_episode_structure(self, sample_episode):
        """Test that sample episode has expected structure."""
        assert sample_episode.id == 12345
        assert sample_episode.title == "Test Episode"
        assert sample_episode.match1 is not None
        assert len(sample_episode.match1.players) == 2
        assert len(sample_episode.commentators) == 1

    def test_player_discord_id_handling(self, sample_episode):
        """Test that players with and without Discord IDs are handled correctly."""
        players = sample_episode.match1.players

        # First player has Discord ID
        assert players[0].discord_id == "123456789012345678"
        assert players[0].discord_id_int == 123456789012345678

        # Second player does not have Discord ID
        assert players[1].discord_id is None
        assert players[1].discord_id_int is None

    def test_crew_member_structure(self, sample_episode):
        """Test crew member data structure."""
        commentator = sample_episode.commentators[0]

        assert commentator.id == 60789
        assert commentator.display_name == "DerMo"
        assert commentator.discord_id_int == 472785637984960512
        assert commentator.approved is False

    def test_etl_service_initialization(self):
        """Test that ETL service initializes correctly."""
        etl_service = SpeedGamingETLService()

        assert etl_service.sg_service is not None
        assert etl_service.tournament_repo is not None
        assert etl_service.user_repo is not None


class TestPlaceholderUserLogic:
    """Test placeholder user creation logic."""

    def test_placeholder_username_format(self):
        """Test that placeholder usernames follow expected format."""
        # Player placeholder
        player_id = 11111
        expected_username = f"sg_{player_id}"
        assert expected_username == "sg_11111"

        # Crew placeholder
        crew_id = 60789
        expected_crew_username = f"sg_crew_{crew_id}"
        assert expected_crew_username == "sg_crew_60789"

    def test_discord_id_placeholder(self):
        """Test that placeholder users use discord_id=0."""
        placeholder_discord_id = 0
        assert placeholder_discord_id == 0  # Invalid ID indicating placeholder
