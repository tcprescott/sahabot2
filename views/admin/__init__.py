"""
Admin views package.

Views used by the admin page.
"""

from views.admin.admin_users import AdminUsersView
from views.admin.admin_organizations import AdminOrganizationsView
from views.admin.admin_settings import AdminSettingsView
from views.admin.admin_racetime_bots import AdminRacetimeBotsView
from views.admin.presets import PresetsView
from views.admin.preset_namespaces import PresetNamespacesView
from views.admin.org_requests import OrgRequestsView

__all__ = [
    'AdminUsersView',
    'AdminOrganizationsView',
    'AdminSettingsView',
    'AdminRacetimeBotsView',
    'PresetsView',
    'PresetNamespacesView',
    'OrgRequestsView',
]
