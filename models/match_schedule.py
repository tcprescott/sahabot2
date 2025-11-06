from __future__ import annotations
from enum import Enum
from tortoise import fields
from tortoise.models import Model


class CrewRole(str, Enum):
    """Enum for crew member roles."""
    COMMENTATOR = "commentator"
    TRACKER = "tracker"
    RESTREAMER = "restreamer"


class DiscordEventFilter(str, Enum):
    """Enum for filtering which matches create Discord events."""
    ALL = "all"  # All scheduled matches
    STREAM_ONLY = "stream_only"  # Only matches with stream_channel assigned
    NONE = "none"  # No matches (same as disabled)


class Tournament(Model):
    id = fields.IntField(pk=True)
    organization = fields.ForeignKeyField('models.Organization', related_name='tournaments')
    name = fields.CharField(max_length=255)
    description = fields.TextField(null=True)
    is_active = fields.BooleanField(default=True)
    tracker_enabled = fields.BooleanField(default=True)

    # RaceTime.gg integration settings
    racetime_bot = fields.ForeignKeyField('models.RacetimeBot', related_name='tournaments', null=True)
    racetime_auto_create_rooms = fields.BooleanField(default=False)
    room_open_minutes_before = fields.IntField(default=60)  # How long before match to open room
    require_racetime_link = fields.BooleanField(default=False)  # Require players to have RaceTime linked
    racetime_default_goal = fields.CharField(max_length=255, null=True)  # Default goal for race rooms
    
    # Race room profile (reusable configuration)
    race_room_profile = fields.ForeignKeyField('models.RaceRoomProfile', related_name='tournaments', null=True)

    # Discord scheduled events integration
    create_scheduled_events = fields.BooleanField(default=False)  # Enable Discord event creation for matches
    scheduled_events_enabled = fields.BooleanField(default=True)  # Master toggle (can disable temporarily)
    discord_event_guilds = fields.ManyToManyField('models.DiscordGuild', related_name='event_tournaments', through='tournament_discord_guilds')  # Guilds to publish events to
    discord_event_filter = fields.CharEnumField(enum_type=DiscordEventFilter, default=DiscordEventFilter.ALL, max_length=20)  # Filter which matches create events
    event_duration_minutes = fields.IntField(default=120)  # Duration of Discord events in minutes (default 120 = 2 hours)

    # SpeedGaming integration
    speedgaming_enabled = fields.BooleanField(default=False)  # Enable SpeedGaming episode import
    speedgaming_event_slug = fields.CharField(max_length=255, null=True)  # SpeedGaming event slug to import from

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

    # RaceTime.gg integration
    racetime_room_slug = fields.CharField(max_length=255, null=True)  # e.g., "alttpr/cool-doge-1234"
    racetime_goal = fields.CharField(max_length=255, null=True)  # Override default tournament goal
    racetime_invitational = fields.BooleanField(default=True)  # Whether room is invite-only
    racetime_auto_create = fields.BooleanField(default=True)  # Whether to auto-create room (or manual)

    # SpeedGaming integration
    speedgaming_episode_id = fields.IntField(null=True, unique=True)  # SpeedGaming episode ID for imported matches

    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    # related fields (reverse relations)
    players: fields.ReverseRelation["MatchPlayers"]
    crew_members: fields.ReverseRelation["Crew"]
    seed: fields.ReverseRelation["MatchSeed"]
    settings_submissions: fields.ReverseRelation["TournamentMatchSettings"]

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
    role = fields.CharEnumField(CrewRole, max_length=100)  # e.g., 'commentator', 'tracker', 'restreamer'
    match = fields.ForeignKeyField('models.Match', related_name='crew_members')
    approved = fields.BooleanField(default=False)
    approved_by = fields.ForeignKeyField('models.User', related_name='approved_crew', null=True)
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)
