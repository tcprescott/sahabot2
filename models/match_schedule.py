from __future__ import annotations
from tortoise import fields
from tortoise.models import Model

class Tournament(Model):
    id = fields.IntField(pk=True)
    organization = fields.ForeignKeyField('models.Organization', related_name='tournaments')
    name = fields.CharField(max_length=255)
    description = fields.TextField(null=True)
    is_active = fields.BooleanField(default=True)
    tracker_enabled = fields.BooleanField(default=True)
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    # related fields (reverse relations)
    players: fields.ReverseRelation["TournamentPlayers"]
    matches: fields.ReverseRelation["Match"]

class Match(Model):
    id = fields.IntField(pk=True)
    tournament = fields.ForeignKeyField('models.Tournament', related_name='matches')
    stream_channel = fields.ForeignKeyField('models.StreamChannel', related_name='matches', null=True)
    scheduled_at = fields.DatetimeField(null=True)
    checked_in_at = fields.DatetimeField(null=True) # now known as "Checked In"
    started_at = fields.DatetimeField(null=True)
    finished_at = fields.DatetimeField(null=True)
    confirmed_at = fields.DatetimeField(null=True)
    comment = fields.TextField(null=True)
    title = fields.CharField(max_length=255, null=True)
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    # related fields (reverse relations)
    players: fields.ReverseRelation["MatchPlayers"]
    crew_members: fields.ReverseRelation["Crew"]
    seed: fields.ReverseRelation["MatchSeed"]

class MatchSeed(Model):
    """Game seed/ROM information for a match (1:1 with Match)."""
    id = fields.IntField(pk=True)
    match = fields.OneToOneField('models.Match', related_name='seed', on_delete=fields.CASCADE)
    url = fields.CharField(max_length=500)
    description = fields.TextField(null=True)
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

class MatchPlayers(Model):
    id = fields.IntField(pk=True)
    match = fields.ForeignKeyField('models.Match', related_name='players')
    user = fields.ForeignKeyField('models.User', related_name='match_players')
    finish_rank = fields.IntField(null=True)
    assigned_station = fields.CharField(max_length=50, null=True)
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

class TournamentPlayers(Model):
    id = fields.IntField(pk=True)
    tournament = fields.ForeignKeyField('models.Tournament', related_name='players')
    user = fields.ForeignKeyField('models.User', related_name='tournament_players')
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

class StreamChannel(Model):
    id = fields.IntField(pk=True)
    organization = fields.ForeignKeyField('models.Organization', related_name='stream_channels')
    name = fields.CharField(max_length=255, unique=True)
    stream_url = fields.CharField(max_length=255, null=True)
    is_active = fields.BooleanField(default=True)
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    # related fields (reverse relations)
    matches: fields.ReverseRelation["Match"]

class Crew(Model):
    id = fields.IntField(pk=True)
    user = fields.ForeignKeyField('models.User', related_name='crew_memberships')
    role = fields.CharField(max_length=100)  # e.g., 'commentator', 'tracker'
    match = fields.ForeignKeyField('models.Match', related_name='crew_members')
    approved = fields.BooleanField(default=False)
    approved_by = fields.ForeignKeyField('models.User', related_name='approved_crew', null=True)
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)
