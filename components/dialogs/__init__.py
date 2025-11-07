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
from components.dialogs.common import BaseDialog, TournamentDialog, ConfirmDialog, ViewYamlDialog

# Admin dialogs
from components.dialogs.admin import (
    UserEditDialog,
    UserAddDialog,
    OrganizationDialog,
    GlobalSettingDialog,
    RacetimeBotAddDialog,
    RacetimeBotEditDialog,
    RacetimeBotOrganizationsDialog,
    ApproveOrgRequestDialog,
    RejectOrgRequestDialog,
    ViewNamespaceDialog,
)

# Organization dialogs
from components.dialogs.organization import (
    MemberPermissionsDialog,
    InviteMemberDialog,
    OrganizationInviteDialog,
    OrgSettingDialog,
    StreamChannelDialog,
    ViewPresetDialog,
)

# Tournament dialogs
from components.dialogs.tournaments import (
    MatchSeedDialog,
    EditMatchDialog,
    CreateMatchDialog,
    SubmitMatchDialog,
    RegisterPlayerDialog,
    AsyncTournamentDialog,
)

# User profile dialogs
from components.dialogs.user_profile import (
    CreateApiKeyDialog,
    DisplayTokenDialog,
    LeaveOrganizationDialog,
    RenameNamespaceDialog,
    AddPermissionDialog,
    EditPermissionDialog,
    ManagePermissionsDialog,
    RequestOrganizationDialog,
)

# Racetime dialogs
# (No racetime dialogs currently)

__all__ = [
    # Common
    'BaseDialog',
    'TournamentDialog',
    'ConfirmDialog',
    'ViewYamlDialog',
    # Admin
    'UserEditDialog',
    'UserAddDialog',
    'OrganizationDialog',
    'GlobalSettingDialog',
    'RacetimeBotAddDialog',
    'RacetimeBotEditDialog',
    'RacetimeBotOrganizationsDialog',
    'ApproveOrgRequestDialog',
    'RejectOrgRequestDialog',
    'ViewNamespaceDialog',
    # Organization
    'OrgSettingDialog',
    'MemberPermissionsDialog',
    'InviteMemberDialog',
    'OrganizationInviteDialog',
    'StreamChannelDialog',
    'ViewPresetDialog',
    # Tournaments
    'SubmitMatchDialog',
    'RegisterPlayerDialog',
    'MatchSeedDialog',
    'EditMatchDialog',
    'CreateMatchDialog',
    'AsyncTournamentDialog',
    # User profile
    'CreateApiKeyDialog',
    'DisplayTokenDialog',
    'LeaveOrganizationDialog',
    'RenameNamespaceDialog',
    'AddPermissionDialog',
    'EditPermissionDialog',
    'ManagePermissionsDialog',
    'RequestOrganizationDialog',
]
