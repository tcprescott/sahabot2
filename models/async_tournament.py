"""
Async Qualifier models.

This module contains models for async qualifiers - a qualifier type where
players complete races asynchronously at their own pace, with scores calculated
based on performance relative to a par time.
"""

from __future__ import annotations
from typing import TYPE_CHECKING, Optional
from datetime import timedelta
from tortoise import fields
from tortoise.models import Model

if TYPE_CHECKING:
    from .organizations import Organization
    from .race_room_profile import RaceRoomProfile


class AsyncQualifier(Model):
    """
    Async Qualifier model.

    Async qualifiers allow players to complete races asynchronously, with each
    player racing permalinks from various pools at their own pace. Scores are
    calculated based on finish time relative to a par time (average of top 5).
    """

    id = fields.IntField(pk=True)
    organization = fields.ForeignKeyField(
        "models.Organization", related_name="async_qualifiers"
    )
    name = fields.CharField(max_length=255)
    description = fields.TextField(null=True)
    is_active = fields.BooleanField(default=True)
    hide_results = fields.BooleanField(
        default=False
    )  # Hide other players' results until qualifier ends
    discord_channel_id = fields.BigIntField(
        null=True, unique=True
    )  # Discord channel for race actions
    runs_per_pool = fields.SmallIntField(
        default=1
    )  # Number of runs each player can do per pool
    max_reattempts = fields.SmallIntField(
        default=-1
    )  # Maximum number of re-attempts allowed per player (-1 = unlimited, 0 = none)
    require_racetime_for_async_runs = fields.BooleanField(
        default=False
    )  # Require RaceTime.gg account for async runs

    # Cached Discord channel permission warnings
    discord_warnings = fields.JSONField(null=True)  # List of permission warning strings
    discord_warnings_checked_at = fields.DatetimeField(
        null=True
    )  # When permissions were last checked

    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    # related fields (reverse relations)
    pools: fields.ReverseRelation["AsyncQualifierPool"]
    races: fields.ReverseRelation["AsyncQualifierRace"]
    live_races: fields.ReverseRelation["AsyncQualifierLiveRace"]
    audit_logs: fields.ReverseRelation["AsyncQualifierAuditLog"]

    class Meta:
        table = "async_qualifiers"


class AsyncQualifierPool(Model):
    """
    Pool of permalinks for an async qualifier.

    A qualifier can have multiple pools, and players must complete a certain
    number of runs from each pool.
    """

    id = fields.IntField(pk=True)
    tournament = fields.ForeignKeyField("models.AsyncQualifier", related_name="pools")
    name = fields.CharField(max_length=255)
    description = fields.TextField(null=True)
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    # related fields (reverse relations)
    permalinks: fields.ReverseRelation["AsyncQualifierPermalink"]

    class Meta:
        table = "async_qualifier_pools"
        unique_together = (("tournament", "name"),)


class AsyncQualifierPermalink(Model):
    """
    Permalink/seed for an async qualifier pool.

    Each permalink can be raced by multiple players. The par time is calculated
    as the average of the top 5 finish times.
    """

    id = fields.IntField(pk=True)
    pool = fields.ForeignKeyField(
        "models.AsyncQualifierPool", related_name="permalinks"
    )
    url = fields.CharField(max_length=500)
    notes = fields.TextField(null=True)
    par_time = fields.FloatField(null=True)  # In seconds, calculated from top 5 times
    par_updated_at = fields.DatetimeField(null=True)
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    # related fields (reverse relations)
    races: fields.ReverseRelation["AsyncQualifierRace"]

    class Meta:
        table = "async_qualifier_permalinks"

    @property
    def par_time_timedelta(self) -> Optional[timedelta]:
        """Get par time as timedelta."""
        if self.par_time is None:
            return None
        return timedelta(seconds=self.par_time)

    @property
    def par_time_formatted(self) -> str:
        """Get formatted par time (HH:MM:SS)."""
        if self.par_time_timedelta is None:
            return "N/A"
        hours, remainder = divmod(int(self.par_time_timedelta.total_seconds()), 3600)
        minutes, seconds = divmod(remainder, 60)
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"


class AsyncQualifierRace(Model):
    """
    Individual race in an async qualifier.

    Tracks a single player's attempt at a permalink, including timing,
    status, and scoring information.
    """

    id = fields.IntField(pk=True)
    tournament = fields.ForeignKeyField("models.AsyncQualifier", related_name="races")
    permalink = fields.ForeignKeyField(
        "models.AsyncQualifierPermalink", related_name="races"
    )
    user = fields.ForeignKeyField("models.User", related_name="async_qualifier_races")

    # Link to live race (if this race was part of a live event)
    live_race = fields.ForeignKeyField(
        "models.AsyncQualifierLiveRace", related_name="participant_races", null=True
    )

    discord_thread_id = fields.BigIntField(null=True)  # Discord thread for this race
    thread_open_time = fields.DatetimeField(null=True)
    thread_timeout_time = fields.DatetimeField(null=True)
    start_time = fields.DatetimeField(null=True)
    end_time = fields.DatetimeField(null=True)
    status = fields.CharField(
        max_length=50, default="pending"
    )  # pending, in_progress, finished, forfeit, disqualified
    reattempted = fields.BooleanField(
        default=False
    )  # True if this race was reattempted
    runner_notes = fields.TextField(null=True)
    runner_vod_url = fields.CharField(max_length=500, null=True)
    score = fields.FloatField(null=True)  # Calculated score based on par time
    score_updated_at = fields.DatetimeField(null=True)

    # Review fields
    review_status = fields.CharField(
        max_length=20, default="pending"
    )  # pending, accepted, rejected
    reviewed_by = fields.ForeignKeyField(
        "models.User", related_name="async_race_reviews", null=True
    )
    reviewed_at = fields.DatetimeField(null=True)
    reviewer_notes = fields.TextField(null=True)
    review_requested_by_user = fields.BooleanField(
        default=False
    )  # True if user flagged for review
    review_request_reason = fields.TextField(
        null=True
    )  # User's reason for requesting review

    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    class Meta:
        table = "async_qualifier_races"

    @property
    def elapsed_time(self) -> Optional[timedelta]:
        """Get elapsed time as timedelta."""
        if self.start_time is None or self.end_time is None:
            return None
        return self.end_time - self.start_time

    @property
    def elapsed_time_formatted(self) -> str:
        """Get formatted elapsed time (HH:MM:SS)."""
        if self.elapsed_time is None:
            return "N/A"
        hours, remainder = divmod(int(self.elapsed_time.total_seconds()), 3600)
        minutes, seconds = divmod(remainder, 60)
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"

    @property
    def status_formatted(self) -> str:
        """Get human-readable status."""
        status_map = {
            "pending": "Pending",
            "in_progress": "In Progress",
            "finished": "Finished",
            "forfeit": "Forfeit",
            "disqualified": "Disqualified",
        }
        return status_map.get(self.status, self.status.title())

    @property
    def score_formatted(self) -> str:
        """Get formatted score."""
        if self.score is None:
            return "N/A"
        return f"{self.score:.3f}"

    @property
    def review_status_formatted(self) -> str:
        """Get human-readable review status."""
        if self.reattempted or self.status != "finished":
            return "N/A"

        status_map = {
            "pending": "Pending",
            "accepted": "Accepted",
            "rejected": "Pending Second Review",
        }
        return status_map.get(self.review_status, self.review_status.title())


class AsyncQualifierLiveRace(Model):
    """
    Live race event for async qualifiers.

    Represents a scheduled race where all eligible participants race the same
    seed simultaneously on RaceTime.gg. Results are automatically recorded.
    Unlike standard async races (individual, thread-based), live races are:
    - Scheduled at specific times
    - Open to all eligible qualifier participants
    - Hosted on RaceTime.gg with automatic result tracking
    """

    id = fields.IntField(pk=True)
    tournament = fields.ForeignKeyField(
        "models.AsyncQualifier", related_name="live_races"
    )
    pool = fields.ForeignKeyField(
        "models.AsyncQualifierPool", related_name="live_races"
    )
    permalink = fields.ForeignKeyField(
        "models.AsyncQualifierPermalink", related_name="live_races", null=True
    )

    # Scheduling
    episode_id = fields.IntField(
        null=True, unique=True
    )  # SpeedGaming episode ID (if applicable)
    scheduled_at = fields.DatetimeField(null=True)  # When race is scheduled to start
    match_title = fields.CharField(max_length=200, null=True)  # Display name for race

    # RaceTime.gg integration
    racetime_slug = fields.CharField(
        max_length=200, null=True, unique=True
    )  # e.g., "alttpr/cool-icerod-1234"
    racetime_goal = fields.CharField(max_length=255, null=True)  # RaceTime.gg goal
    room_open_time = fields.DatetimeField(null=True)  # When room was opened

    # Room configuration (optional override of tournament's profile)
    # If null, inherits from tournament.race_room_profile or org default profile
    race_room_profile = fields.ForeignKeyField(
        "models.RaceRoomProfile", related_name="live_races", null=True
    )

    # Status tracking
    status = fields.CharField(max_length=45, default="scheduled")
    # scheduled: Room not yet created
    # pending: Room created, waiting for race to start
    # in_progress: Race started
    # finished: Race completed
    # cancelled: Race cancelled

    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    # related fields (reverse relations)
    participant_races: fields.ReverseRelation["AsyncQualifierRace"]

    class Meta:
        table = "async_qualifier_live_races"

    @property
    def racetime_url(self) -> Optional[str]:
        """Get RaceTime.gg URL for this race."""
        if not self.racetime_slug:
            return None
        return f"https://racetime.gg/{self.racetime_slug}"

    async def get_effective_profile(self) -> Optional[RaceRoomProfile]:
        """
        Get the effective race room profile for this live race.

        Priority:
        1. Live race's specific profile (if set)
        2. Tournament's profile (if set)
        3. Organization's default profile
        4. None (use system defaults)

        Returns:
            RaceRoomProfile if found, None otherwise
        """
        # Check if this live race has a specific profile
        await self.fetch_related("race_room_profile")
        if self.race_room_profile is not None:
            return self.race_room_profile

        # Check if tournament has a profile
        await self.fetch_related("tournament__race_room_profile")
        if self.tournament.race_room_profile is not None:
            return self.tournament.race_room_profile

        # Get org default profile (no auth check needed for internal model method)
        from application.repositories.race_room_profile_repository import (
            RaceRoomProfileRepository,
        )

        await self.fetch_related("tournament__organization")
        repo = RaceRoomProfileRepository()
        return await repo.get_default_for_org(self.tournament.organization_id)


class AsyncQualifierAuditLog(Model):
    """
    Audit log for async qualifier actions.

    Tracks all significant actions in async qualifiers for accountability
    and debugging.
    """

    id = fields.IntField(pk=True)
    tournament = fields.ForeignKeyField(
        "models.AsyncQualifier", related_name="audit_logs"
    )
    user = fields.ForeignKeyField(
        "models.User", related_name="async_qualifier_audit_logs", null=True
    )
    action = fields.CharField(
        max_length=100
    )  # e.g., 'create_thread', 'race_start', 'race_finish'
    details = fields.TextField(null=True)
    created_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "async_qualifier_audit_logs"
