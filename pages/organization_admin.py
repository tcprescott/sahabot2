"""
Organization-specific admin pages.

Accessible by SUPERADMIN/ADMIN or members with an org-level admin role.
"""

from nicegui import ui
from components.base_page import BasePage
from application.services.organizations.organization_service import OrganizationService
from application.services.tournaments import TournamentService
from views.organization import (
    OrganizationOverviewView,
    OrganizationMembersView,
    OrganizationPermissionsView,
    OrganizationSettingsView,
    OrganizationTournamentsView,
    OrganizationAsyncQualifiersView,
    OrganizationStreamChannelsView,
    OrganizationScheduledTasksView,
    DiscordServersView,
    RaceRoomProfileManagementView,
    RacerVerificationConfigView,
    OrganizationAuditLogsView,
)


def _create_org_sidebar(base: BasePage, org_id: int, active: str, can_admin: bool, can_manage_tournaments: bool):
    """Create common sidebar for organization admin pages."""
    sidebar_items = [
        base.create_nav_link("Back to Organization", "arrow_back", f"/org/{org_id}"),
        base.create_separator(),
    ]
    
    # Admin-only items
    if can_admin:
        sidebar_items.extend([
            base.create_nav_link("Overview", "dashboard", f"/orgs/{org_id}/admin", active=(active == "overview")),
            base.create_nav_link("Members", "people", f"/orgs/{org_id}/admin/members", active=(active == "members")),
            base.create_nav_link("Permissions", "security", f"/orgs/{org_id}/admin/permissions", active=(active == "permissions")),
            base.create_nav_link("Stream Channels", "podcasts", f"/orgs/{org_id}/admin/stream-channels", active=(active == "stream-channels")),
            base.create_nav_link("Scheduled Tasks", "schedule", f"/orgs/{org_id}/admin/scheduled-tasks", active=(active == "scheduled-tasks")),
            base.create_nav_link("Discord Servers", "forum", f"/orgs/{org_id}/admin/discord-servers", active=(active == "discord-servers")),
            base.create_nav_link("Racer Verification", "verified", f"/orgs/{org_id}/admin/racer-verification", active=(active == "racer-verification")),
            base.create_nav_link("Audit Logs", "history", f"/orgs/{org_id}/admin/audit-logs", active=(active == "audit-logs")),
            base.create_separator(),
        ])
    
    # Tournament manager items (available to both admins and tournament managers)
    sidebar_items.extend([
        base.create_nav_link("Tournaments", "emoji_events", f"/orgs/{org_id}/admin/tournaments", active=(active == "tournaments")),
        base.create_nav_link("Async Qualifiers", "schedule", f"/orgs/{org_id}/admin/async-qualifiers", active=(active == "async-qualifiers")),
        base.create_nav_link("Race Room Profiles", "settings", f"/orgs/{org_id}/admin/race-room-profiles", active=(active == "race-room-profiles")),
    ])
    
    # Settings (admin only)
    if can_admin:
        sidebar_items.extend([
            base.create_separator(),
            base.create_nav_link("Settings", "settings", f"/orgs/{org_id}/admin/settings", active=(active == "settings")),
        ])
    
    return sidebar_items


async def _get_org_context(organization_id: int):
    """Get organization and check permissions."""
    from middleware.auth import DiscordAuthService
    
    user = await DiscordAuthService.get_current_user()
    service = OrganizationService()
    
    # Check permissions
    allowed_admin = await service.user_can_admin_org(user, organization_id)
    allowed_tournaments = await service.user_can_manage_tournaments(user, organization_id)
    allowed = allowed_admin or allowed_tournaments
    
    if not allowed:
        return None, None, False, False, "You do not have access to administer this organization."
    
    # Get organization
    org = await service.get_organization(organization_id)
    if not org:
        return None, None, False, False, "Organization not found"
    
    return user, org, allowed_admin, allowed_tournaments, None


def register():
    """Register organization admin routes."""

    @ui.page("/orgs/{organization_id}/admin")
    async def org_overview_page(organization_id: int):
        """Organization overview page."""
        base = BasePage.authenticated_page(title="Organization Admin")

        async def content(page: BasePage):
            """Render overview content."""
            user, org, can_admin, can_manage, error = await _get_org_context(organization_id)
            
            if error:
                ui.notify(error, color="negative")
                ui.navigate.to(f"/org/{organization_id}")
                return
            
            if not can_admin:
                ui.notify("Overview is only accessible to organization admins", color="negative")
                ui.navigate.to(f"/org/{organization_id}")
                return
            
            view = OrganizationOverviewView(org, user)
            await view.render()

        sidebar_items = _create_org_sidebar(base, organization_id, "overview", True, False)
        await base.render(content, sidebar_items)

    @ui.page("/orgs/{organization_id}/admin/members")
    async def org_members_page(organization_id: int):
        """Organization members page."""
        base = BasePage.authenticated_page(title="Members")

        async def content(page: BasePage):
            """Render members content."""
            user, org, can_admin, can_manage, error = await _get_org_context(organization_id)
            
            if error:
                ui.notify(error, color="negative")
                ui.navigate.to(f"/org/{organization_id}")
                return
            
            if not can_admin:
                ui.notify("Members management requires admin permissions", color="negative")
                ui.navigate.to(f"/org/{organization_id}")
                return
            
            view = OrganizationMembersView(org, user)
            await view.render()

        user, org, can_admin, _, _ = await _get_org_context(organization_id)
        sidebar_items = _create_org_sidebar(base, organization_id, "members", can_admin, False)
        await base.render(content, sidebar_items)

    @ui.page("/orgs/{organization_id}/admin/permissions")
    async def org_permissions_page(organization_id: int):
        """Organization permissions page."""
        base = BasePage.authenticated_page(title="Permissions")

        async def content(page: BasePage):
            """Render permissions content."""
            user, org, can_admin, can_manage, error = await _get_org_context(organization_id)
            
            if error:
                ui.notify(error, color="negative")
                ui.navigate.to(f"/org/{organization_id}")
                return
            
            if not can_admin:
                ui.notify("Permissions management requires admin permissions", color="negative")
                ui.navigate.to(f"/org/{organization_id}")
                return
            
            view = OrganizationPermissionsView(org, user)
            await view.render()

        user, org, can_admin, _, _ = await _get_org_context(organization_id)
        sidebar_items = _create_org_sidebar(base, organization_id, "permissions", can_admin, False)
        await base.render(content, sidebar_items)

    @ui.page("/orgs/{organization_id}/admin/settings")
    async def org_settings_page(organization_id: int):
        """Organization settings page."""
        base = BasePage.authenticated_page(title="Organization Settings")

        async def content(page: BasePage):
            """Render settings content."""
            user, org, can_admin, can_manage, error = await _get_org_context(organization_id)
            
            if error:
                ui.notify(error, color="negative")
                ui.navigate.to(f"/org/{organization_id}")
                return
            
            if not can_admin:
                ui.notify("Settings management requires admin permissions", color="negative")
                ui.navigate.to(f"/org/{organization_id}")
                return
            
            view = OrganizationSettingsView(org, user)
            await view.render()

        user, org, can_admin, _, _ = await _get_org_context(organization_id)
        sidebar_items = _create_org_sidebar(base, organization_id, "settings", can_admin, False)
        await base.render(content, sidebar_items)

    @ui.page("/orgs/{organization_id}/admin/tournaments")
    async def org_tournaments_page(organization_id: int):
        """Organization tournaments page."""
        base = BasePage.authenticated_page(title="Tournaments")

        async def content(page: BasePage):
            """Render tournaments content."""
            user, org, can_admin, can_manage, error = await _get_org_context(organization_id)
            
            if error:
                ui.notify(error, color="negative")
                ui.navigate.to(f"/org/{organization_id}")
                return
            
            view = OrganizationTournamentsView(user, org, TournamentService())
            await view.render()

        user, org, can_admin, can_manage, _ = await _get_org_context(organization_id)
        sidebar_items = _create_org_sidebar(base, organization_id, "tournaments", can_admin, can_manage)
        await base.render(content, sidebar_items)

    @ui.page("/orgs/{organization_id}/admin/async-qualifiers")
    async def org_async_qualifiers_page(organization_id: int):
        """Organization async qualifiers page."""
        base = BasePage.authenticated_page(title="Async Qualifiers")

        async def content(page: BasePage):
            """Render async qualifiers content."""
            user, org, can_admin, can_manage, error = await _get_org_context(organization_id)
            
            if error:
                ui.notify(error, color="negative")
                ui.navigate.to(f"/org/{organization_id}")
                return
            
            view = OrganizationAsyncQualifiersView(org, user)
            await view.render()

        user, org, can_admin, can_manage, _ = await _get_org_context(organization_id)
        sidebar_items = _create_org_sidebar(base, organization_id, "async-qualifiers", can_admin, can_manage)
        await base.render(content, sidebar_items)

    @ui.page("/orgs/{organization_id}/admin/stream-channels")
    async def org_stream_channels_page(organization_id: int):
        """Organization stream channels page."""
        base = BasePage.authenticated_page(title="Stream Channels")

        async def content(page: BasePage):
            """Render stream channels content."""
            user, org, can_admin, can_manage, error = await _get_org_context(organization_id)
            
            if error:
                ui.notify(error, color="negative")
                ui.navigate.to(f"/org/{organization_id}")
                return
            
            if not can_admin:
                ui.notify("Stream channels management requires admin permissions", color="negative")
                ui.navigate.to(f"/org/{organization_id}")
                return
            
            view = OrganizationStreamChannelsView(org, user)
            await view.render()

        user, org, can_admin, _, _ = await _get_org_context(organization_id)
        sidebar_items = _create_org_sidebar(base, organization_id, "stream-channels", can_admin, False)
        await base.render(content, sidebar_items)

    @ui.page("/orgs/{organization_id}/admin/scheduled-tasks")
    async def org_scheduled_tasks_page(organization_id: int):
        """Organization scheduled tasks page."""
        base = BasePage.authenticated_page(title="Scheduled Tasks")

        async def content(page: BasePage):
            """Render scheduled tasks content."""
            user, org, can_admin, can_manage, error = await _get_org_context(organization_id)
            
            if error:
                ui.notify(error, color="negative")
                ui.navigate.to(f"/org/{organization_id}")
                return
            
            if not can_admin:
                ui.notify("Scheduled tasks management requires admin permissions", color="negative")
                ui.navigate.to(f"/org/{organization_id}")
                return
            
            view = OrganizationScheduledTasksView(org, user)
            await view.render()

        user, org, can_admin, _, _ = await _get_org_context(organization_id)
        sidebar_items = _create_org_sidebar(base, organization_id, "scheduled-tasks", can_admin, False)
        await base.render(content, sidebar_items)

    @ui.page("/orgs/{organization_id}/admin/discord-servers")
    async def org_discord_servers_page(organization_id: int):
        """Organization Discord servers page."""
        base = BasePage.authenticated_page(title="Discord Servers")

        async def content(page: BasePage):
            """Render Discord servers content."""
            user, org, can_admin, can_manage, error = await _get_org_context(organization_id)
            
            if error:
                ui.notify(error, color="negative")
                ui.navigate.to(f"/org/{organization_id}")
                return
            
            if not can_admin:
                ui.notify("Discord servers management requires admin permissions", color="negative")
                ui.navigate.to(f"/org/{organization_id}")
                return
            
            view = DiscordServersView(user, org)
            await view.render()

        user, org, can_admin, _, _ = await _get_org_context(organization_id)
        sidebar_items = _create_org_sidebar(base, organization_id, "discord-servers", can_admin, False)
        await base.render(content, sidebar_items)

    @ui.page("/orgs/{organization_id}/admin/race-room-profiles")
    async def org_race_room_profiles_page(organization_id: int):
        """Organization race room profiles page."""
        base = BasePage.authenticated_page(title="Race Room Profiles")

        async def content(page: BasePage):
            """Render race room profiles content."""
            user, org, can_admin, can_manage, error = await _get_org_context(organization_id)
            
            if error:
                ui.notify(error, color="negative")
                ui.navigate.to(f"/org/{organization_id}")
                return
            
            view = RaceRoomProfileManagementView(user, org)
            await view.render()

        user, org, can_admin, can_manage, _ = await _get_org_context(organization_id)
        sidebar_items = _create_org_sidebar(base, organization_id, "race-room-profiles", can_admin, can_manage)
        await base.render(content, sidebar_items)

    @ui.page("/orgs/{organization_id}/admin/racer-verification")
    async def org_racer_verification_page(organization_id: int):
        """Organization racer verification page."""
        base = BasePage.authenticated_page(title="Racer Verification")

        async def content(page: BasePage):
            """Render racer verification content."""
            user, org, can_admin, can_manage, error = await _get_org_context(organization_id)
            
            if error:
                ui.notify(error, color="negative")
                ui.navigate.to(f"/org/{organization_id}")
                return
            
            if not can_admin:
                ui.notify("Racer verification management requires admin permissions", color="negative")
                ui.navigate.to(f"/org/{organization_id}")
                return
            
            view = RacerVerificationConfigView(org.id, user)
            await view.render()

        user, org, can_admin, _, _ = await _get_org_context(organization_id)
        sidebar_items = _create_org_sidebar(base, organization_id, "racer-verification", can_admin, False)
        await base.render(content, sidebar_items)

    @ui.page("/orgs/{organization_id}/admin/audit-logs")
    async def org_audit_logs_page(organization_id: int):
        """Organization audit logs page."""
        base = BasePage.authenticated_page(title="Audit Logs")

        async def content(page: BasePage):
            """Render audit logs content."""
            user, org, can_admin, can_manage, error = await _get_org_context(organization_id)
            
            if error:
                ui.notify(error, color="negative")
                ui.navigate.to(f"/org/{organization_id}")
                return
            
            if not can_admin:
                ui.notify("Audit logs requires admin permissions", color="negative")
                ui.navigate.to(f"/org/{organization_id}")
                return
            
            view = OrganizationAuditLogsView(org, user)
            await view.render()

        user, org, can_admin, _, _ = await _get_org_context(organization_id)
        sidebar_items = _create_org_sidebar(base, organization_id, "audit-logs", can_admin, False)
        await base.render(content, sidebar_items)
