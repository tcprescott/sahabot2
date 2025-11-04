"""
Views package for SahaBot2.

This package contains view modules for different sections of the application.
Views are organized into subdirectories based on which pages use them:
- admin: Views used by the admin page
- organization: Views used by the organization admin page
- tournament_admin: Views used by the tournament admin page
- user_profile: Views used by the user profile page
- tournaments: Views used by the tournaments page
"""

# Re-export all views for backward compatibility
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
    OrganizationTournamentsView,
    OrganizationStreamChannelsView,
)

from views.tournament_admin import (
    TournamentOverviewView,
    TournamentMatchesView,
    TournamentPlayersView,
    TournamentRacetimeSettingsView,
    TournamentSettingsView,
)

from views.user_profile import (
    ProfileInfoView,
    ApiKeysView,
    UserOrganizationsView,
)

from views.tournaments import (
    TournamentOrgSelectView,
    EventScheduleView,
    MyMatchesView,
    MySettingsView,
)

__all__ = [
    # Admin views
    'AdminUsersView',
    'AdminOrganizationsView',
    'AdminSettingsView',
    # Organization views
    'OrganizationOverviewView',
    'OrganizationMembersView',
    'OrganizationPermissionsView',
    'OrganizationSettingsView',
    'OrganizationTournamentsView',
    'OrganizationStreamChannelsView',
    # Tournament Admin views
    'TournamentOverviewView',
    'TournamentMatchesView',
    'TournamentPlayersView',
    'TournamentRacetimeSettingsView',
    'TournamentSettingsView',
    # User Profile views
    'ProfileInfoView',
    'ApiKeysView',
    'UserOrganizationsView',
    # Tournament views
    'TournamentOrgSelectView',
    'EventScheduleView',
    'MyMatchesView',
    'MySettingsView',
]
