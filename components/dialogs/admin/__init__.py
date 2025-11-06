"""Admin-related dialogs."""

from components.dialogs.admin.user_edit_dialog import UserEditDialog
from components.dialogs.admin.user_add_dialog import UserAddDialog
from components.dialogs.admin.global_setting_dialog import GlobalSettingDialog
from components.dialogs.admin.organization_dialog import OrganizationDialog
from components.dialogs.admin.racetime_bot_add_dialog import RacetimeBotAddDialog
from components.dialogs.admin.racetime_bot_edit_dialog import RacetimeBotEditDialog
from components.dialogs.admin.racetime_bot_organizations_dialog import RacetimeBotOrganizationsDialog
from components.dialogs.admin.approve_org_request_dialog import ApproveOrgRequestDialog
from components.dialogs.admin.reject_org_request_dialog import RejectOrgRequestDialog
from components.dialogs.admin.view_namespace_dialog import ViewNamespaceDialog
from components.dialogs.admin.racetime_unlink_dialog import RacetimeUnlinkDialog
from components.dialogs.admin.twitch_unlink_dialog import TwitchUnlinkDialog
from components.dialogs.admin.motd_dialog import MOTDDialog

__all__ = [
    'UserEditDialog',
    'UserAddDialog',
    'GlobalSettingDialog',
    'OrganizationDialog',
    'RacetimeBotAddDialog',
    'RacetimeBotEditDialog',
    'RacetimeBotOrganizationsDialog',
    'ApproveOrgRequestDialog',
    'RejectOrgRequestDialog',
    'ViewNamespaceDialog',
    'RacetimeUnlinkDialog',
    'TwitchUnlinkDialog',
    'MOTDDialog',
]
