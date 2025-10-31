"""
Views package for SahaBot2.

This package contains view modules for different sections of the application.
Views are organized into subdirectories based on which pages use them:
- home: Views used by the home page
- admin: Views used by the admin page
- organization: Views used by the organization admin page
"""

# Re-export all views for backward compatibility
from views.home import (
    OverviewView,
    ScheduleView,
    UsersView,
    ReportsView,
    SettingsView,
    FavoritesView,
    ToolsView,
    HelpView,
    AboutView,
    WelcomeView,
    ArchiveView,
    LoremIpsumView,
)

from views.admin import (
    AdminUsersView,
    AdminOrganizationsView,
    AdminSettingsView,
)

from views.organization import (
    OrganizationOverviewView,
    OrganizationMembersView,
    OrganizationPermissionsView,
    OrganizationSettingsView,
)

__all__ = [
    # Home views
    'OverviewView',
    'ScheduleView',
    'UsersView',
    'ReportsView',
    'SettingsView',
    'FavoritesView',
    'ToolsView',
    'HelpView',
    'AboutView',
    'WelcomeView',
    'ArchiveView',
    'LoremIpsumView',
    # Admin views
    'AdminUsersView',
    'AdminOrganizationsView',
    'AdminSettingsView',
    # Organization views
    'OrganizationOverviewView',
    'OrganizationMembersView',
    'OrganizationPermissionsView',
    'OrganizationSettingsView',
]
