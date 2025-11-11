"""
Global admin pages (SUPERADMIN and ADMIN only).
"""

from nicegui import ui
from components.base_page import BasePage
from views.admin import (
    AdminUsersView,
    AdminOrganizationsView,
    AdminSettingsView,
    AdminRacetimeBotsView,
    PresetsView,
    PresetNamespacesView,
    OrgRequestsView,
    ScheduledTasksView,
    RacetimeAccountsView,
    AdminAuditLogsView,
    AdminLogsView,
)


def _create_admin_sidebar(base: BasePage, active: str):
    """Create common sidebar for admin pages."""
    return [
        base.create_nav_link("Back to Home", "arrow_back", "/"),
        base.create_separator(),
        base.create_nav_link("Overview", "dashboard", "/admin", active=(active == "overview")),
        base.create_nav_link("Users", "people", "/admin/users", active=(active == "users")),
        base.create_nav_link("Organizations", "business", "/admin/organizations", active=(active == "organizations")),
        base.create_nav_link("Org Requests", "how_to_reg", "/admin/org-requests", active=(active == "org-requests")),
        base.create_separator(),
        base.create_nav_link("RaceTime Bots", "smart_toy", "/admin/racetime-bots", active=(active == "racetime-bots")),
        base.create_nav_link("Presets", "tune", "/admin/presets", active=(active == "presets")),
        base.create_nav_link("Namespaces", "folder", "/admin/namespaces", active=(active == "namespaces")),
        base.create_separator(),
        base.create_nav_link("Scheduled Tasks", "schedule", "/admin/scheduled-tasks", active=(active == "scheduled-tasks")),
        base.create_nav_link("Audit Logs", "history", "/admin/audit-logs", active=(active == "audit-logs")),
        base.create_nav_link("Application Logs", "description", "/admin/logs", active=(active == "logs")),
        base.create_separator(),
        base.create_nav_link("Settings", "settings", "/admin/settings", active=(active == "settings")),
    ]


def register():
    """Register admin routes."""

    @ui.page("/admin")
    async def admin_overview_page():
        """Admin overview/dashboard page."""
        base = BasePage.admin_page(title="Admin Panel")

        async def content(page: BasePage):
            """Render overview content."""
            with ui.element('div').classes('card'):
                with ui.element('div').classes('card-header'):
                    ui.label('Admin Panel').classes('text-xl')
                with ui.element('div').classes('card-body'):
                    ui.label('Select a section from the sidebar to manage.')

        sidebar_items = _create_admin_sidebar(base, "overview")
        await base.render(content, sidebar_items)

    @ui.page("/admin/users")
    async def admin_users_page():
        """Admin users management page."""
        base = BasePage.admin_page(title="User Management")

        async def content(page: BasePage):
            """Render users content."""
            view = AdminUsersView(page.user)
            await view.render()

        sidebar_items = _create_admin_sidebar(base, "users")
        await base.render(content, sidebar_items)

    @ui.page("/admin/organizations")
    async def admin_organizations_page():
        """Admin organizations management page."""
        base = BasePage.admin_page(title="Organizations")

        async def content(page: BasePage):
            """Render organizations content."""
            view = AdminOrganizationsView(page.user)
            await view.render()

        sidebar_items = _create_admin_sidebar(base, "organizations")
        await base.render(content, sidebar_items)

    @ui.page("/admin/org-requests")
    async def admin_org_requests_page():
        """Admin organization requests page."""
        base = BasePage.admin_page(title="Organization Requests")

        async def content(page: BasePage):
            """Render org requests content."""
            view = OrgRequestsView(page.user)
            await view.render()

        sidebar_items = _create_admin_sidebar(base, "org-requests")
        await base.render(content, sidebar_items)

    @ui.page("/admin/racetime-bots")
    async def admin_racetime_bots_page():
        """Admin RaceTime bots management page."""
        base = BasePage.admin_page(title="RaceTime Bots")

        async def content(page: BasePage):
            """Render RaceTime bots content."""
            view = AdminRacetimeBotsView(page.user)
            await view.render()

        sidebar_items = _create_admin_sidebar(base, "racetime-bots")
        await base.render(content, sidebar_items)

    @ui.page("/admin/presets")
    async def admin_presets_page():
        """Admin presets management page."""
        base = BasePage.admin_page(title="Randomizer Presets")

        async def content(page: BasePage):
            """Render presets content."""
            from application.services.randomizer.randomizer_preset_service import RandomizerPresetService
            service = RandomizerPresetService()
            view = PresetsView(page.user, service)
            await view.render()

        sidebar_items = _create_admin_sidebar(base, "presets")
        await base.render(content, sidebar_items)

    @ui.page("/admin/namespaces")
    async def admin_namespaces_page():
        """Admin namespaces management page."""
        base = BasePage.admin_page(title="Preset Namespaces")

        async def content(page: BasePage):
            """Render namespaces content."""
            view = PresetNamespacesView(page.user)
            await view.render()

        sidebar_items = _create_admin_sidebar(base, "namespaces")
        await base.render(content, sidebar_items)

    @ui.page("/admin/scheduled-tasks")
    async def admin_scheduled_tasks_page():
        """Admin scheduled tasks page."""
        base = BasePage.admin_page(title="Scheduled Tasks")

        async def content(page: BasePage):
            """Render scheduled tasks content."""
            view = ScheduledTasksView(page.user)
            await view.render()

        sidebar_items = _create_admin_sidebar(base, "scheduled-tasks")
        await base.render(content, sidebar_items)

    @ui.page("/admin/audit-logs")
    async def admin_audit_logs_page():
        """Admin audit logs page."""
        base = BasePage.admin_page(title="Audit Logs")

        async def content(page: BasePage):
            """Render audit logs content."""
            view = AdminAuditLogsView(page.user)
            await view.render()

        sidebar_items = _create_admin_sidebar(base, "audit-logs")
        await base.render(content, sidebar_items)

    @ui.page("/admin/logs")
    async def admin_application_logs_page():
        """Admin application logs page."""
        base = BasePage.admin_page(title="Application Logs")

        async def content(page: BasePage):
            """Render logs content."""
            view = AdminLogsView(page.user)
            await view.render()

        sidebar_items = _create_admin_sidebar(base, "logs")
        await base.render(content, sidebar_items)

    @ui.page("/admin/settings")
    async def admin_settings_page():
        """Admin settings page."""
        base = BasePage.admin_page(title="Admin Settings")

        async def content(page: BasePage):
            """Render settings content."""
            view = AdminSettingsView(page.user)
            await view.render()

        sidebar_items = _create_admin_sidebar(base, "settings")
        await base.render(content, sidebar_items)
