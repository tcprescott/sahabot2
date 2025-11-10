"""
Admin page for SahaBot2.

This module provides administrative functionality using BasePage's dynamic content loading.

The page uses a single route with dynamic content switching via sidebar navigation:
- Overview: Dashboard with welcome message and statistics
- Users: User management interface
- Settings: Application settings

This pattern is reusable for other multi-section pages via BasePage.
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
    AdminAuditLogsView,
    AdminLogsView,
)
from views.home import overview
from application.services.randomizer.randomizer_preset_service import (
    RandomizerPresetService,
)


def register():
    """Register admin page routes."""

    @ui.page("/admin")
    async def admin_page():
        """Admin dashboard page with dynamic content switching."""
        base = BasePage.admin_page(title="SahaBot2 - Admin")

        async def content(page: BasePage):
            """Render the admin page with dynamic content container."""

            # Define content loader functions
            async def load_overview():
                """Load the overview content."""
                container = page.get_dynamic_content_container() or ui.element(
                    "div"
                ).classes("page-container")
                container.clear()
                with container:
                    # Header
                    with ui.element("div").classes("card"):
                        with ui.element("div").classes("card-header"):
                            ui.label("Admin Dashboard").classes("text-2xl font-bold")
                    with ui.element("div").classes("card-body"):
                        ui.label(f"Welcome, {page.user.get_display_name()}").classes(
                            "text-primary"
                        )
                        ui.label(
                            f"Permission Level: {page.user.permission.name}"
                        ).classes(
                            "text-secondary"
                        )  # Render overview
                    await overview.OverviewView.render(page.user)

            # Register content loaders
            page.register_content_loader("overview", load_overview)
            page.register_instance_view("users", lambda: AdminUsersView(page.user))
            page.register_instance_view("organizations", lambda: AdminOrganizationsView(page.user))
            page.register_instance_view("org-requests", lambda: OrgRequestsView(page.user))
            page.register_instance_view("racetime-bots", lambda: AdminRacetimeBotsView(page.user))
            page.register_instance_view("presets", lambda: PresetsView(page.user, RandomizerPresetService()))
            page.register_instance_view("namespaces", lambda: PresetNamespacesView(page.user))
            page.register_instance_view("scheduled-tasks", lambda: ScheduledTasksView(page.user))
            page.register_instance_view("audit-logs", lambda: AdminAuditLogsView(page.user))
            page.register_instance_view("logs", lambda: AdminLogsView(page.user))
            page.register_instance_view("settings", lambda: AdminSettingsView(page.user))

            # Load initial content only if no view parameter was specified
            if not page.initial_view:
                await load_overview()

        # Create sidebar items with dynamic content loaders
        sidebar_items = [
            base.create_nav_link("Home", "home", "/"),
            base.create_separator(),
        ]
        sidebar_items.extend(base.create_sidebar_items([
            ("Overview", "dashboard", "overview"),
            ("Users", "people", "users"),
            ("Organizations", "domain", "organizations"),
            ("Org Requests", "pending_actions", "org-requests"),
            ("RaceTime Bots", "smart_toy", "racetime-bots"),
            ("Presets", "code", "presets"),
            ("Namespaces", "folder", "namespaces"),
            ("Scheduled Tasks", "schedule", "scheduled-tasks"),
            ("Audit Logs", "history", "audit-logs"),
            ("Application Logs", "terminal", "logs"),
            ("Settings", "settings", "settings"),
        ]))

        await base.render(content, sidebar_items, use_dynamic_content=True)
