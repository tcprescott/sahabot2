"""
User Profile pages.

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


def _create_profile_sidebar(base: BasePage, active: str):
    """Create common sidebar for profile pages."""
    sidebar_items = [
        base.create_nav_link("Back to Home", "home", "/"),
        base.create_separator(),
        base.create_nav_link("Profile Info", "person", "/profile", active=(active == "profile")),
        base.create_nav_link("Profile Settings", "settings", "/profile/settings", active=(active == "settings")),
        base.create_nav_link("Notifications", "notifications", "/profile/notifications", active=(active == "notifications")),
        base.create_nav_link("API Keys", "vpn_key", "/profile/api-keys", active=(active == "api-keys")),
        base.create_nav_link("Organizations", "business", "/profile/organizations", active=(active == "organizations")),
        base.create_nav_link("Preset Namespaces", "folder", "/profile/preset-namespaces", active=(active == "preset-namespaces")),
        base.create_separator(),
        base.create_nav_link("RaceTime Account", "link", "/profile/racetime", active=(active == "racetime")),
        base.create_nav_link("Twitch Account", "videocam", "/profile/twitch", active=(active == "twitch")),
        base.create_nav_link("Racer Verification", "verified", "/profile/racer-verification", active=(active == "racer-verification")),
    ]
    return sidebar_items


def register():
    """Register user profile page routes."""

    @ui.page("/profile")
    async def profile_info_page():
        """Profile information page."""
        base = BasePage.authenticated_page(title="My Profile")

        async def content(page: BasePage):
            """Render profile info content."""
            view = ProfileInfoView(page.user)
            await view.render()

        sidebar_items = _create_profile_sidebar(base, "profile")
        await base.render(content, sidebar_items)

    @ui.page("/profile/settings")
    async def profile_settings_page():
        """Profile settings page."""
        base = BasePage.authenticated_page(title="Profile Settings")

        async def content(page: BasePage):
            """Render profile settings content."""
            view = ProfileSettingsView(page.user)
            await view.render()

        sidebar_items = _create_profile_sidebar(base, "settings")
        await base.render(content, sidebar_items)

    @ui.page("/profile/api-keys")
    async def api_keys_page():
        """API keys management page."""
        base = BasePage.authenticated_page(title="API Keys")

        async def content(page: BasePage):
            """Render API keys content."""
            view = ApiKeysView(page.user)
            await view.render()

        sidebar_items = _create_profile_sidebar(base, "api-keys")
        await base.render(content, sidebar_items)

    @ui.page("/profile/organizations")
    async def organizations_page():
        """User organizations page."""
        base = BasePage.authenticated_page(title="My Organizations")

        async def content(page: BasePage):
            """Render organizations content."""
            view = UserOrganizationsView(page.user)
            await view.render()

        sidebar_items = _create_profile_sidebar(base, "organizations")
        await base.render(content, sidebar_items)

    @ui.page("/profile/racetime")
    async def racetime_account_page():
        """RaceTime account linking page."""
        base = BasePage.authenticated_page(title="RaceTime Account")

        async def content(page: BasePage):
            """Render RaceTime account content."""
            view = RacetimeAccountView(page.user)
            await view.render()

        sidebar_items = _create_profile_sidebar(base, "racetime")
        await base.render(content, sidebar_items)

    @ui.page("/profile/twitch")
    async def twitch_account_page():
        """Twitch account linking page."""
        base = BasePage.authenticated_page(title="Twitch Account")

        async def content(page: BasePage):
            """Render Twitch account content."""
            view = TwitchAccountView(page.user)
            await view.render()

        sidebar_items = _create_profile_sidebar(base, "twitch")
        await base.render(content, sidebar_items)

    @ui.page("/profile/preset-namespaces")
    async def preset_namespaces_page():
        """Preset namespaces page."""
        base = BasePage.authenticated_page(title="Preset Namespaces")

        async def content(page: BasePage):
            """Render preset namespaces content."""
            view = PresetNamespacesView(page.user)
            await view.render()

        sidebar_items = _create_profile_sidebar(base, "preset-namespaces")
        await base.render(content, sidebar_items)

    @ui.page("/profile/notifications")
    async def notifications_page():
        """Notification preferences page."""
        base = BasePage.authenticated_page(title="Notification Preferences")

        async def content(page: BasePage):
            """Render notification preferences content."""
            view = NotificationPreferencesView(page.user)
            await view.render()

        sidebar_items = _create_profile_sidebar(base, "notifications")
        await base.render(content, sidebar_items)

    @ui.page("/profile/racer-verification")
    async def racer_verification_page():
        """Racer verification page."""
        base = BasePage.authenticated_page(title="Racer Verification")

        async def content(page: BasePage):
            """Render racer verification content."""
            view = RacerVerificationView(page.user)
            await view.render()

        sidebar_items = _create_profile_sidebar(base, "racer-verification")
        await base.render(content, sidebar_items)
