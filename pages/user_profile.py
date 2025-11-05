"""
User Profile page.

Allow users to view and manage their profile information, API keys, and organizations.
"""

from nicegui import ui
from components.base_page import BasePage
from views.user_profile import (
    ProfileInfoView,
    ProfileSettingsView,
    ApiKeysView,
    UserOrganizationsView,
    RacetimeAccountView,
    RacetimeRacesView,
    PresetNamespacesView,
    NotificationPreferencesView,
)


def register():
    """Register user profile page route."""

    @ui.page('/profile')
    async def profile_page():
        """
        User profile page with dynamic content switching.

        Displays profile information, API keys management, and organization memberships.
        """
        # Create authenticated page
        base = BasePage.authenticated_page(title="My Profile")

        async def content(page: BasePage):
            """Render profile page content."""
            # Register content loaders for dynamic switching
            page.register_content_loader('profile', page.create_instance_view_loader(lambda: ProfileInfoView(page.user)))
            page.register_content_loader('settings', page.create_instance_view_loader(lambda: ProfileSettingsView(page.user)))
            page.register_content_loader('api-keys', page.create_instance_view_loader(lambda: ApiKeysView(page.user)))
            page.register_content_loader('organizations', page.create_instance_view_loader(lambda: UserOrganizationsView(page.user)))
            page.register_content_loader('racetime', page.create_instance_view_loader(lambda: RacetimeAccountView(page.user)))
            page.register_content_loader('racetime-races', page.create_instance_view_loader(lambda: RacetimeRacesView(page.user)))
            page.register_content_loader('preset-namespaces', page.create_instance_view_loader(lambda: PresetNamespacesView(page.user)))
            page.register_content_loader('notifications', page.create_instance_view_loader(lambda: NotificationPreferencesView(page.user)))

            # Load initial content only if no view parameter was specified
            if not page.initial_view:
                await page.create_instance_view_loader(lambda: ProfileInfoView(page.user))()

        # Create sidebar items
        sidebar_items = [
            base.create_nav_link('Back to Home', 'home', '/'),
            base.create_separator(),
            base.create_sidebar_item_with_loader('Profile Info', 'person', 'profile'),
            base.create_sidebar_item_with_loader('Profile Settings', 'settings', 'settings'),
            base.create_sidebar_item_with_loader('Notifications', 'notifications', 'notifications'),
            base.create_sidebar_item_with_loader('API Keys', 'vpn_key', 'api-keys'),
            base.create_sidebar_item_with_loader('Organizations', 'business', 'organizations'),
            base.create_sidebar_item_with_loader('Preset Namespaces', 'folder', 'preset-namespaces'),
            base.create_separator(),
            base.create_sidebar_item_with_loader('RaceTime Account', 'link', 'racetime'),
            base.create_sidebar_item_with_loader('Race History', 'sports_score', 'racetime-races'),
        ]

        await base.render(content, sidebar_items, use_dynamic_content=True)
