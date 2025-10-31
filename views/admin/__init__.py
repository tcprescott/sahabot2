"""
Admin views package.

Views used by the admin page.
"""

from views.admin.admin_users import AdminUsersView
from views.admin.admin_organizations import AdminOrganizationsView
from views.admin.admin_settings import AdminSettingsView

__all__ = [
    'AdminUsersView',
    'AdminOrganizationsView',
    'AdminSettingsView',
]
