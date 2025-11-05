"""
Admin views package.

Views used by the admin page.
"""

from views.admin.admin_users import AdminUsersView
from views.admin.admin_organizations import AdminOrganizationsView
from views.admin.admin_settings import AdminSettingsView
from views.admin.admin_racetime_bots import AdminRacetimeBotsView
from views.admin.admin_racetime_chat_commands import AdminRacetimeChatCommandsView
from views.admin.presets import PresetsView
from views.admin.preset_namespaces import PresetNamespacesView
from views.admin.org_requests import OrgRequestsView
from views.admin.scheduled_tasks import ScheduledTasksView
from views.admin.racetime_accounts import RacetimeAccountsView

__all__ = [
    'AdminUsersView',
    'AdminOrganizationsView',
    'AdminSettingsView',
    'AdminRacetimeBotsView',
    'AdminRacetimeChatCommandsView',
    'PresetsView',
    'PresetNamespacesView',
    'OrgRequestsView',
    'ScheduledTasksView',
    'RacetimeAccountsView',
]
