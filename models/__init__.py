"""
Database models package for SahaBot2.

This package contains all Tortoise ORM models for the application.
"""

from models.user import (
    User,
    Permission,
    SYSTEM_USER_ID,
    is_system_user_id,
    is_authenticated_user_id,
    get_user_id_description,
)
from models.audit_log import AuditLog
from models.api_token import ApiToken
from models.match_schedule import Tournament, Match, MatchPlayers, MatchSeed, StreamChannel, TournamentPlayers, Crew, CrewRole, DiscordEventFilter
from models.tournament_match_settings import TournamentMatchSettings
from models.organizations import Organization, OrganizationMember, OrganizationPermission
from models.organization_invite import OrganizationInvite
from models.organization_request import OrganizationRequest
from models.settings import GlobalSetting, OrganizationSetting
from models.discord_guild import DiscordGuild
from models.async_tournament import (
    AsyncTournament,
    AsyncTournamentPool,
    AsyncTournamentPermalink,
    AsyncTournamentRace,
    AsyncTournamentLiveRace,
    AsyncTournamentAuditLog,
)
from models.scheduled_task import ScheduledTask, TaskType, ScheduleType
from models.tournament_usage import TournamentUsage
from models.randomizer_preset import RandomizerPreset
from models.preset_namespace import PresetNamespace
from models.preset_namespace_permission import PresetNamespacePermission
from models.racetime_bot import RacetimeBot, RacetimeBotOrganization, BotStatus
from models.racetime_chat_command import RacetimeChatCommand, CommandScope, CommandResponseType
from models.race_room_profile import RaceRoomProfile
from models.racer_verification import RacerVerification, UserRacerVerification
from models.notification_subscription import NotificationSubscription, NotificationMethod, NotificationEventType
from models.notification_log import NotificationLog, NotificationDeliveryStatus
from models.discord_scheduled_event import DiscordScheduledEvent
from models.organization_feature_flag import OrganizationFeatureFlag, FeatureFlag
from models.authorization import (
    OrganizationRole,
    OrganizationMemberRole,
    PolicyStatement,
    RolePolicy,
    UserPolicy,
)

__all__ = [
    'User',
    'Permission',
    'AuditLog',
    'ApiToken',
    'Organization',
    'OrganizationMember',
    'OrganizationPermission',
    'OrganizationInvite',
    'OrganizationRequest',
    'DiscordGuild',
    'GlobalSetting',
    'OrganizationSetting',
    'Tournament',
    'TournamentPlayers',
    'Match',
    'MatchPlayers',
    'MatchSeed',
    'TournamentMatchSettings',
    'StreamChannel',
    'Crew',
    'CrewRole',
    'DiscordEventFilter',
    'AsyncTournament',
    'AsyncTournamentPool',
    'AsyncTournamentPermalink',
    'AsyncTournamentRace',
    'AsyncTournamentLiveRace',
    'AsyncTournamentAuditLog',
    'ScheduledTask',
    'TaskType',
    'ScheduleType',
    'TournamentUsage',
    'RandomizerPreset',
    'PresetNamespace',
    'PresetNamespacePermission',
    'RacetimeBot',
    'RacetimeBotOrganization',
    'BotStatus',
    'RacetimeChatCommand',
    'CommandScope',
    'CommandResponseType',
    'RaceRoomProfile',
    'RacerVerification',
    'UserRacerVerification',
    'NotificationSubscription',
    'NotificationMethod',
    'NotificationEventType',
    'NotificationLog',
    'NotificationDeliveryStatus',
    'DiscordScheduledEvent',
    'OrganizationFeatureFlag',
    'FeatureFlag',
    # Authorization models
    'OrganizationRole',
    'OrganizationMemberRole',
    'PolicyStatement',
    'RolePolicy',
    'UserPolicy',
    # Helper functions/constants
    'SYSTEM_USER_ID',
    'is_system_user_id',
    'is_authenticated_user_id',
    'get_user_id_description',
]
