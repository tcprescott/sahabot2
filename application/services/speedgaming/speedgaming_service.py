"""
SpeedGaming API service.

This service handles API calls to SpeedGaming.org for fetching episode and event data.
"""

import httpx
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class SpeedGamingPlayer:
    """SpeedGaming player data from API."""
    id: int
    display_name: str
    discord_id: Optional[str]  # Discord ID as string from API
    discord_tag: Optional[str]  # Discord username#discriminator
    public_stream: Optional[str]
    streaming_from: Optional[str]

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SpeedGamingPlayer":
        """Create SpeedGamingPlayer from API response."""
        return cls(
            id=data.get("id", 0),
            display_name=data.get("displayName", ""),
            discord_id=data.get("discordId") or None,
            discord_tag=data.get("discordTag") or None,
            public_stream=data.get("publicStream") or None,
            streaming_from=data.get("streamingFrom") or None,
        )

    @property
    def discord_id_int(self) -> Optional[int]:
        """Get Discord ID as integer if available."""
        if self.discord_id:
            try:
                return int(self.discord_id)
            except (ValueError, TypeError):
                return None
        return None


@dataclass
class SpeedGamingCrewMember:
    """SpeedGaming crew member (commentator, tracker, etc.) from API."""
    id: int
    display_name: str
    discord_id: Optional[str]
    discord_tag: Optional[str]
    language: str
    ready: bool
    approved: bool
    public_stream: Optional[str]

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SpeedGamingCrewMember":
        """Create SpeedGamingCrewMember from API response."""
        return cls(
            id=data.get("id", 0),
            display_name=data.get("displayName", ""),
            discord_id=data.get("discordId") or None,
            discord_tag=data.get("discordTag") or None,
            language=data.get("language", "en"),
            ready=data.get("ready", False),
            approved=data.get("approved", False),
            public_stream=data.get("publicStream") or None,
        )

    @property
    def discord_id_int(self) -> Optional[int]:
        """Get Discord ID as integer if available."""
        if self.discord_id:
            try:
                return int(self.discord_id)
            except (ValueError, TypeError):
                return None
        return None


@dataclass
class SpeedGamingMatch:
    """SpeedGaming match data from API."""
    id: int
    title: str
    players: List[SpeedGamingPlayer]

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> Optional["SpeedGamingMatch"]:
        """Create SpeedGamingMatch from API response."""
        if not data:
            return None

        players = [SpeedGamingPlayer.from_dict(p) for p in data.get("players", [])]

        return cls(
            id=data.get("id", 0),
            title=data.get("title", ""),
            players=players,
        )


@dataclass
class SpeedGamingEvent:
    """SpeedGaming event data from API."""
    id: int
    name: str
    slug: str
    game: str
    active: bool

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SpeedGamingEvent":
        """Create SpeedGamingEvent from API response."""
        return cls(
            id=data.get("id", 0),
            name=data.get("name", ""),
            slug=data.get("slug", ""),
            game=data.get("game", ""),
            active=data.get("active", True),
        )


@dataclass
class SpeedGamingChannel:
    """SpeedGaming broadcast channel data from API."""
    id: int
    name: str
    slug: str
    language: str

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SpeedGamingChannel":
        """Create SpeedGamingChannel from API response."""
        return cls(
            id=data.get("id", 0),
            name=data.get("name", ""),
            slug=data.get("slug", ""),
            language=data.get("language", "en"),
        )


@dataclass
class SpeedGamingEpisode:
    """
    SpeedGaming episode data from API.

    Represents a scheduled match/episode on SpeedGaming.
    """
    id: int
    title: str
    when: datetime  # Scheduled time in UTC
    approved: bool
    length: int  # Duration in minutes
    match1: Optional[SpeedGamingMatch]
    match2: Optional[SpeedGamingMatch]
    event: SpeedGamingEvent
    channels: List[SpeedGamingChannel]
    commentators: List[SpeedGamingCrewMember]
    trackers: List[SpeedGamingCrewMember]
    broadcasters: List[SpeedGamingCrewMember]

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SpeedGamingEpisode":
        """Create SpeedGamingEpisode from API response."""
        # Parse datetime (format: "2022-11-06T18:00:00+00:00")
        when_str = data.get("when", "")
        when = datetime.fromisoformat(when_str.replace("+00:00", "+00:00"))
        if when.tzinfo is None:
            when = when.replace(tzinfo=timezone.utc)

        # Parse matches
        match1 = SpeedGamingMatch.from_dict(data.get("match1")) if data.get("match1") else None
        match2 = SpeedGamingMatch.from_dict(data.get("match2")) if data.get("match2") else None

        # Parse event
        event = SpeedGamingEvent.from_dict(data.get("event", {}))

        # Parse channels
        channels = [SpeedGamingChannel.from_dict(c) for c in data.get("channels", [])]

        # Parse crew
        commentators = [SpeedGamingCrewMember.from_dict(c) for c in data.get("commentators", [])]
        trackers = [SpeedGamingCrewMember.from_dict(t) for t in data.get("trackers", [])]
        broadcasters = [SpeedGamingCrewMember.from_dict(b) for b in data.get("broadcasters", [])]

        return cls(
            id=data.get("id", 0),
            title=data.get("title", ""),
            when=when,
            approved=data.get("approved", False),
            length=data.get("length", 60),
            match1=match1,
            match2=match2,
            event=event,
            channels=channels,
            commentators=commentators,
            trackers=trackers,
            broadcasters=broadcasters,
        )


class SpeedGamingService:
    """
    Service for interacting with SpeedGaming API.

    Provides methods for fetching episodes and event data from SpeedGaming.org.
    """

    def __init__(self):
        """Initialize the SpeedGaming API service."""
        self.base_url = "https://speedgaming.org/api"
        self.timeout = 30.0  # Request timeout in seconds

    async def get_episode(self, episode_id: int) -> Optional[SpeedGamingEpisode]:
        """
        Fetch episode details from SpeedGaming API.

        Args:
            episode_id: SpeedGaming episode ID

        Returns:
            SpeedGamingEpisode if found, None otherwise

        Raises:
            httpx.HTTPError: If API request fails
        """
        url = f"{self.base_url}/episode/?id={episode_id}"

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(url)

                if response.status_code == 404:
                    logger.info("Episode %s not found", episode_id)
                    return None

                if response.status_code != 200:
                    logger.error(
                        "SpeedGaming API request failed: GET %s - status %s",
                        url,
                        response.status_code
                    )
                    response.raise_for_status()

                data = response.json()
                episode = SpeedGamingEpisode.from_dict(data)
                logger.info("Fetched episode %s: %s", episode_id, episode.title)
                return episode

        except httpx.HTTPError as e:
            logger.error("Failed to fetch episode %s: %s", episode_id, e)
            raise

    async def get_upcoming_episodes_by_event(
        self,
        event_slug: str,
        from_datetime: Optional[datetime] = None,
        to_datetime: Optional[datetime] = None
    ) -> List[SpeedGamingEpisode]:
        """
        Fetch episodes for a specific event within a date range.

        Args:
            event_slug: SpeedGaming event slug (e.g., "alttprleague")
            from_datetime: Start of date range (defaults to 2 hours ago)
            to_datetime: End of date range (defaults to 7 days from now)

        Returns:
            List of SpeedGamingEpisode objects within date range

        Raises:
            httpx.HTTPError: If API request fails
        """
        # Default to 2 hours ago to 7 days from now
        now = datetime.now(timezone.utc)
        if from_datetime is None:
            from_datetime = now - timedelta(hours=2)
        if to_datetime is None:
            to_datetime = now + timedelta(days=7)

        url = f"{self.base_url}/schedule/"  # Trailing slash required by SpeedGaming API
        params = {
            "event": event_slug,
            "from": from_datetime.isoformat(),
            "to": to_datetime.isoformat(),
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(url, params=params)

                if response.status_code != 200:
                    logger.error(
                        "SpeedGaming API request failed: GET %s - status %s",
                        url,
                        response.status_code
                    )
                    response.raise_for_status()

                data = response.json()

                # API might return a list or dict with 'episodes' key
                if isinstance(data, list):
                    episodes_data = data
                else:
                    episodes_data = data.get("episodes", [])

                episodes = [SpeedGamingEpisode.from_dict(ep) for ep in episodes_data]
                logger.info(
                    "Fetched %s episodes for event '%s' from %s to %s",
                    len(episodes),
                    event_slug,
                    from_datetime.isoformat(),
                    to_datetime.isoformat()
                )
                return episodes

        except httpx.HTTPError as e:
            logger.error("Failed to fetch episodes for event '%s': %s", event_slug, e)
            raise
