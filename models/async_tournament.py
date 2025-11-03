"""
Async Tournament models.

This module contains models for async tournaments - a tournament type where
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


class AsyncTournament(Model):
    """
    Async Tournament model.

    Async tournaments allow players to complete races asynchronously, with each
    player racing permalinks from various pools at their own pace. Scores are
    calculated based on finish time relative to a par time (average of top 5).
    """
    id = fields.IntField(pk=True)
    organization = fields.ForeignKeyField('models.Organization', related_name='async_tournaments')
    name = fields.CharField(max_length=255)
    description = fields.TextField(null=True)
    is_active = fields.BooleanField(default=True)
    discord_channel_id = fields.BigIntField(null=True, unique=True)  # Discord channel for race actions
    runs_per_pool = fields.SmallIntField(default=1)  # Number of runs each player can do per pool
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    # related fields (reverse relations)
    pools: fields.ReverseRelation["AsyncTournamentPool"]
    races: fields.ReverseRelation["AsyncTournamentRace"]
    audit_logs: fields.ReverseRelation["AsyncTournamentAuditLog"]

    class Meta:
        table = "async_tournaments"


class AsyncTournamentPool(Model):
    """
    Pool of permalinks for an async tournament.

    A tournament can have multiple pools, and players must complete a certain
    number of runs from each pool.
    """
    id = fields.IntField(pk=True)
    tournament = fields.ForeignKeyField('models.AsyncTournament', related_name='pools')
    name = fields.CharField(max_length=255)
    description = fields.TextField(null=True)
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    # related fields (reverse relations)
    permalinks: fields.ReverseRelation["AsyncTournamentPermalink"]

    class Meta:
        table = "async_tournament_pools"
        unique_together = (('tournament', 'name'),)


class AsyncTournamentPermalink(Model):
    """
    Permalink/seed for an async tournament pool.

    Each permalink can be raced by multiple players. The par time is calculated
    as the average of the top 5 finish times.
    """
    id = fields.IntField(pk=True)
    pool = fields.ForeignKeyField('models.AsyncTournamentPool', related_name='permalinks')
    url = fields.CharField(max_length=500)
    notes = fields.TextField(null=True)
    par_time = fields.FloatField(null=True)  # In seconds, calculated from top 5 times
    par_updated_at = fields.DatetimeField(null=True)
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    # related fields (reverse relations)
    races: fields.ReverseRelation["AsyncTournamentRace"]

    class Meta:
        table = "async_tournament_permalinks"

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


class AsyncTournamentRace(Model):
    """
    Individual race in an async tournament.

    Tracks a single player's attempt at a permalink, including timing,
    status, and scoring information.
    """
    id = fields.IntField(pk=True)
    tournament = fields.ForeignKeyField('models.AsyncTournament', related_name='races')
    permalink = fields.ForeignKeyField('models.AsyncTournamentPermalink', related_name='races')
    user = fields.ForeignKeyField('models.User', related_name='async_tournament_races')
    discord_thread_id = fields.BigIntField(null=True)  # Discord thread for this race
    thread_open_time = fields.DatetimeField(null=True)
    thread_timeout_time = fields.DatetimeField(null=True)
    start_time = fields.DatetimeField(null=True)
    end_time = fields.DatetimeField(null=True)
    status = fields.CharField(max_length=50, default='pending')  # pending, in_progress, finished, forfeit, disqualified
    reattempted = fields.BooleanField(default=False)  # True if this race was reattempted
    runner_notes = fields.TextField(null=True)
    runner_vod_url = fields.CharField(max_length=500, null=True)
    score = fields.FloatField(null=True)  # Calculated score based on par time
    score_updated_at = fields.DatetimeField(null=True)
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    class Meta:
        table = "async_tournament_races"

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
            'pending': 'Pending',
            'in_progress': 'In Progress',
            'finished': 'Finished',
            'forfeit': 'Forfeit',
            'disqualified': 'Disqualified'
        }
        return status_map.get(self.status, self.status.title())

    @property
    def score_formatted(self) -> str:
        """Get formatted score."""
        if self.score is None:
            return "N/A"
        return f"{self.score:.3f}"


class AsyncTournamentAuditLog(Model):
    """
    Audit log for async tournament actions.

    Tracks all significant actions in async tournaments for accountability
    and debugging.
    """
    id = fields.IntField(pk=True)
    tournament = fields.ForeignKeyField('models.AsyncTournament', related_name='audit_logs')
    user = fields.ForeignKeyField('models.User', related_name='async_tournament_audit_logs', null=True)
    action = fields.CharField(max_length=100)  # e.g., 'create_thread', 'race_start', 'race_finish'
    details = fields.TextField(null=True)
    created_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "async_tournament_audit_logs"
