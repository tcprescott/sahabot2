"""
Dialog components package.

Dialogs are organized into subdirectories based on the views that use them:
- admin/: Dialogs used by admin views (users, organizations, settings)
- organization/: Dialogs used by organization views (members, settings, stream channels)
- tournaments/: Dialogs used by tournament views (matches, players, schedule)
- user_profile/: Dialogs used by user profile views (API keys, organizations)
- common/: Dialogs used across multiple views (base dialog, confirm dialog)

For backward compatibility, all dialogs are re-exported from this module.
"""

# Common dialogs (used across multiple views)
from components.dialogs.common import BaseDialog, TournamentDialog, ConfirmDialog

# Admin dialogs
from components.dialogs.admin import (
    UserEditDialog,
    UserAddDialog,
    OrganizationDialog,
    GlobalSettingDialog,
    RacetimeBotAddDialog,
    RacetimeBotEditDialog,
    RacetimeBotOrganizationsDialog,
)

# Organization dialogs
from components.dialogs.organization import (
    MemberPermissionsDialog,
    InviteMemberDialog,
    OrganizationInviteDialog,
    OrgSettingDialog,
    StreamChannelDialog,
)

# Tournament dialogs
from components.dialogs.tournaments import (
    MatchSeedDialog,
    EditMatchDialog,
    SubmitMatchDialog,
    RegisterPlayerDialog,
    AsyncTournamentDialog,
)

# User profile dialogs
from components.dialogs.user_profile import (
    CreateApiKeyDialog,
    DisplayTokenDialog,
    LeaveOrganizationDialog,
)

__all__ = [
    # Common
    'BaseDialog',
    'TournamentDialog',
    'ConfirmDialog',
    # Admin
    'UserEditDialog',
    'UserAddDialog',
    'OrganizationDialog',
    'GlobalSettingDialog',
    'RacetimeBotAddDialog',
    'RacetimeBotEditDialog',
    'RacetimeBotOrganizationsDialog',
    # Organization
    'OrgSettingDialog',
    'MemberPermissionsDialog',
    'InviteMemberDialog',
    'OrganizationInviteDialog',
    'StreamChannelDialog',
    # Tournaments
    'SubmitMatchDialog',
    'RegisterPlayerDialog',
    'MatchSeedDialog',
    'EditMatchDialog',
    'AsyncTournamentDialog',
    # User profile
    'CreateApiKeyDialog',
    'DisplayTokenDialog',
    'LeaveOrganizationDialog',
]
