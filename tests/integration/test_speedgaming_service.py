"""
Tests for SpeedGaming API service.
"""

from datetime import datetime, timezone
from application.services.speedgaming.speedgaming_service import (
    SpeedGamingService,
    SpeedGamingPlayer,
    SpeedGamingCrewMember,
    SpeedGamingMatch,
    SpeedGamingEvent,
    SpeedGamingChannel,
    SpeedGamingEpisode,
)


class TestSpeedGamingDataClasses:
    """Test SpeedGaming data classes."""

    def test_player_from_dict(self):
        """Test creating SpeedGamingPlayer from API response."""
        data = {
            "id": 11111,
            "displayName": "synack",
            "discordId": "123456789",
            "discordTag": "Synack#1337",
            "publicStream": "the_synack",
            "streamingFrom": "the_synack",
        }

        player = SpeedGamingPlayer.from_dict(data)

        assert player.id == 11111
        assert player.display_name == "synack"
        assert player.discord_id == "123456789"
        assert player.discord_id_int == 123456789
        assert player.discord_tag == "Synack#1337"
        assert player.public_stream == "the_synack"
        assert player.streaming_from == "the_synack"

    def test_player_from_dict_no_discord_id(self):
        """Test creating SpeedGamingPlayer without Discord ID."""
        data = {
            "id": 11111,
            "displayName": "synack",
            "discordId": "",
            "discordTag": "Synack#1337",
            "publicStream": "",
            "streamingFrom": "the_synack",
        }

        player = SpeedGamingPlayer.from_dict(data)

        assert player.id == 11111
        assert player.display_name == "synack"
        assert player.discord_id is None
        assert player.discord_id_int is None

    def test_crew_member_from_dict(self):
        """Test creating SpeedGamingCrewMember from API response."""
        data = {
            "id": 60789,
            "displayName": "DerMo",
            "discordId": "472785637984960512",
            "discordTag": "Mo1988#1772",
            "language": "en",
            "ready": False,
            "approved": False,
            "publicStream": "DerMo1988",
        }

        crew = SpeedGamingCrewMember.from_dict(data)

        assert crew.id == 60789
        assert crew.display_name == "DerMo"
        assert crew.discord_id == "472785637984960512"
        assert crew.discord_id_int == 472785637984960512
        assert crew.language == "en"
        assert crew.ready is False
        assert crew.approved is False

    def test_match_from_dict(self):
        """Test creating SpeedGamingMatch from API response."""
        data = {
            "id": 32812,
            "title": "Standard",
            "players": [
                {
                    "id": 11111,
                    "displayName": "synack",
                    "discordId": "123456789",
                    "discordTag": "Synack#1337",
                    "publicStream": "",
                    "streamingFrom": "the_synack",
                }
            ],
        }

        match = SpeedGamingMatch.from_dict(data)

        assert match.id == 32812
        assert match.title == "Standard"
        assert len(match.players) == 1
        assert match.players[0].display_name == "synack"

    def test_event_from_dict(self):
        """Test creating SpeedGamingEvent from API response."""
        data = {
            "id": 573,
            "name": "Bot Testing 123",
            "slug": "test",
            "game": "Bot Testing 123",
            "active": True,
        }

        event = SpeedGamingEvent.from_dict(data)

        assert event.id == 573
        assert event.name == "Bot Testing 123"
        assert event.slug == "test"
        assert event.game == "Bot Testing 123"
        assert event.active is True

    def test_channel_from_dict(self):
        """Test creating SpeedGamingChannel from API response."""
        data = {
            "id": 25,
            "name": "SpeedGaming",
            "slug": "speedgaming",
            "language": "en",
        }

        channel = SpeedGamingChannel.from_dict(data)

        assert channel.id == 25
        assert channel.name == "SpeedGaming"
        assert channel.slug == "speedgaming"
        assert channel.language == "en"

    def test_episode_from_dict(self):
        """Test creating SpeedGamingEpisode from API response."""
        data = {
            "id": 1,
            "title": "",
            "when": "2022-11-06T18:00:00+00:00",
            "approved": True,
            "length": 60,
            "match1": {
                "id": 32812,
                "title": "Standard",
                "players": [
                    {
                        "id": 11111,
                        "displayName": "synack",
                        "discordId": "123456789",
                        "discordTag": "Synack#1337",
                        "publicStream": "",
                        "streamingFrom": "the_synack",
                    }
                ],
            },
            "match2": None,
            "event": {
                "id": 573,
                "name": "Bot Testing 123",
                "slug": "test",
                "game": "Bot Testing 123",
                "active": True,
            },
            "channels": [
                {
                    "id": 25,
                    "name": "SpeedGaming",
                    "slug": "speedgaming",
                    "language": "en",
                }
            ],
            "commentators": [
                {
                    "id": 60789,
                    "displayName": "DerMo",
                    "discordId": "472785637984960512",
                    "discordTag": "Mo1988#1772",
                    "language": "en",
                    "ready": False,
                    "approved": False,
                    "publicStream": "DerMo1988",
                }
            ],
            "trackers": [],
            "broadcasters": [],
        }

        episode = SpeedGamingEpisode.from_dict(data)

        assert episode.id == 1
        assert episode.title == ""
        assert episode.when == datetime(2022, 11, 6, 18, 0, 0, tzinfo=timezone.utc)
        assert episode.approved is True
        assert episode.length == 60
        assert episode.match1 is not None
        assert episode.match1.title == "Standard"
        assert len(episode.match1.players) == 1
        assert episode.match2 is None
        assert episode.event.slug == "test"
        assert len(episode.channels) == 1
        assert len(episode.commentators) == 1
        assert len(episode.trackers) == 0


class TestSpeedGamingService:
    """Test SpeedGaming API service."""

    def test_service_initialization(self):
        """Test service initializes correctly."""
        service = SpeedGamingService()

        assert service.base_url == "https://speedgaming.org/api"
        assert service.timeout == 30.0
