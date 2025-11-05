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
    AdminRacetimeChatCommandsView,
    PresetsView,
    PresetNamespacesView,
    OrgRequestsView,
    ScheduledTasksView,
    RacetimeAccountsView,
)
from views.home import overview
from application.services.randomizer_preset_service import RandomizerPresetService


def register():
    """Register admin page routes."""

    @ui.page('/admin')
    async def admin_page():
        """Admin dashboard page with dynamic content switching."""
        base = BasePage.admin_page(title="SahaBot2 - Admin")

        async def content(page: BasePage):
            """Render the admin page with dynamic content container."""
            # Define content loader functions
            async def load_overview():
                """Load the overview content."""
                container = page.get_dynamic_content_container() or ui.element('div').classes('page-container')
                container.clear()
                with container:
                    # Header
                    with ui.element('div').classes('card'):
                        with ui.element('div').classes('card-header'):
                            ui.label('Admin Dashboard').classes('text-2xl font-bold')
                    with ui.element('div').classes('card-body'):
                        ui.label(f'Welcome, {page.user.get_display_name()}').classes('text-primary')
                        ui.label(f'Permission Level: {page.user.permission.name}').classes('text-secondary')                    # Render overview
                    await overview.OverviewView.render(page.user)

            # Register content loaders
            page.register_content_loader('overview', load_overview)
            page.register_content_loader('users', page.create_instance_view_loader(lambda: AdminUsersView(page.user)))
            page.register_content_loader('organizations', page.create_instance_view_loader(lambda: AdminOrganizationsView(page.user)))
            page.register_content_loader('org-requests', page.create_instance_view_loader(lambda: OrgRequestsView(page.user)))
            page.register_content_loader('racetime-bots', page.create_instance_view_loader(lambda: AdminRacetimeBotsView(page.user)))
            page.register_content_loader('racetime-chat-commands', page.create_instance_view_loader(lambda: AdminRacetimeChatCommandsView(page.user)))
            page.register_content_loader('racetime-accounts', page.create_instance_view_loader(lambda: RacetimeAccountsView(page.user)))
            page.register_content_loader('presets', page.create_instance_view_loader(lambda: PresetsView(page.user, RandomizerPresetService())))
            page.register_content_loader('namespaces', page.create_instance_view_loader(lambda: PresetNamespacesView(page.user)))
            page.register_content_loader('scheduled-tasks', page.create_instance_view_loader(lambda: ScheduledTasksView(page.user)))
            page.register_content_loader('settings', page.create_instance_view_loader(lambda: AdminSettingsView(page.user)))

            # Load initial content only if no view parameter was specified
            if not page.initial_view:
                await load_overview()

        # Create sidebar items with dynamic content loaders
        sidebar_items = [
            base.create_nav_link('Home', 'home', '/'),
            base.create_separator(),
            base.create_sidebar_item_with_loader('Overview', 'dashboard', 'overview'),
            base.create_sidebar_item_with_loader('Users', 'people', 'users'),
            base.create_sidebar_item_with_loader('Organizations', 'domain', 'organizations'),
            base.create_sidebar_item_with_loader('Org Requests', 'pending_actions', 'org-requests'),
            base.create_sidebar_item_with_loader('RaceTime Bots', 'smart_toy', 'racetime-bots'),
            base.create_sidebar_item_with_loader('Chat Commands', 'chat', 'racetime-chat-commands'),
            base.create_sidebar_item_with_loader('RaceTime Accounts', 'link', 'racetime-accounts'),
            base.create_sidebar_item_with_loader('Presets', 'code', 'presets'),
            base.create_sidebar_item_with_loader('Namespaces', 'folder', 'namespaces'),
            base.create_sidebar_item_with_loader('Scheduled Tasks', 'schedule', 'scheduled-tasks'),
            base.create_sidebar_item_with_loader('Settings', 'settings', 'settings'),
        ]

        await base.render(content, sidebar_items, use_dynamic_content=True)
