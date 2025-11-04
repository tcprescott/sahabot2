"""Admin-related dialogs."""

from components.dialogs.admin.user_edit_dialog import UserEditDialog
from components.dialogs.admin.user_add_dialog import UserAddDialog
from components.dialogs.admin.global_setting_dialog import GlobalSettingDialog
from components.dialogs.admin.organization_dialog import OrganizationDialog
from components.dialogs.admin.racetime_bot_add_dialog import RacetimeBotAddDialog
from components.dialogs.admin.racetime_bot_edit_dialog import RacetimeBotEditDialog
from components.dialogs.admin.racetime_bot_organizations_dialog import RacetimeBotOrganizationsDialog

__all__ = [
    'UserEditDialog',
    'UserAddDialog',
    'GlobalSettingDialog',
    'OrganizationDialog',
    'RacetimeBotAddDialog',
    'RacetimeBotEditDialog',
    'RacetimeBotOrganizationsDialog',
]
