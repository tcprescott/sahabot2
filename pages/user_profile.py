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
    TwitchAccountView,
    PresetNamespacesView,
    NotificationPreferencesView,
    RacerVerificationView,
)


def register():
    """Register user profile page route."""

    @ui.page("/profile")
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
            page.register_instance_view("profile", lambda: ProfileInfoView(page.user))
            page.register_instance_view("settings", lambda: ProfileSettingsView(page.user))
            page.register_instance_view("api-keys", lambda: ApiKeysView(page.user))
            page.register_instance_view("organizations", lambda: UserOrganizationsView(page.user))
            page.register_instance_view("racetime", lambda: RacetimeAccountView(page.user))
            page.register_instance_view("twitch", lambda: TwitchAccountView(page.user))
            page.register_instance_view("preset-namespaces", lambda: PresetNamespacesView(page.user))
            page.register_instance_view("notifications", lambda: NotificationPreferencesView(page.user))
            page.register_instance_view("racer-verification", lambda: RacerVerificationView(page.user))

            # Load initial content only if no view parameter was specified
            if not page.initial_view:
                await page.create_instance_view_loader(
                    lambda: ProfileInfoView(page.user)
                )()

        # Create sidebar items
        sidebar_items = [
            base.create_nav_link("Back to Home", "home", "/"),
            base.create_separator(),
        ]
        sidebar_items.extend(base.create_sidebar_items([
            ("Profile Info", "person", "profile"),
            ("Profile Settings", "settings", "settings"),
            ("Notifications", "notifications", "notifications"),
            ("API Keys", "vpn_key", "api-keys"),
            ("Organizations", "business", "organizations"),
            ("Preset Namespaces", "folder", "preset-namespaces"),
        ]))
        sidebar_items.append(base.create_separator())
        sidebar_items.extend(base.create_sidebar_items([
            ("RaceTime Account", "link", "racetime"),
            ("Twitch Account", "videocam", "twitch"),
            ("Racer Verification", "verified", "racer-verification"),
        ]))

        await base.render(content, sidebar_items, use_dynamic_content=True)
