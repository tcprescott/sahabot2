"""
User Profile page.

Allow users to view and manage their profile information, API keys, and organizations.
"""

from nicegui import ui
from components.base_page import BasePage
from views.user_profile import ProfileInfoView, ApiKeysView, UserOrganizationsView


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
            page.register_content_loader('api-keys', page.create_instance_view_loader(lambda: ApiKeysView(page.user)))
            page.register_content_loader('organizations', page.create_instance_view_loader(lambda: UserOrganizationsView(page.user)))

            # Load initial content (profile info)
            await page.create_instance_view_loader(lambda: ProfileInfoView(page.user))()

        # Create sidebar items
        sidebar_items = [
            base.create_sidebar_item_with_loader('Profile Info', 'person', 'profile'),
            base.create_sidebar_item_with_loader('API Keys', 'vpn_key', 'api-keys'),
            base.create_sidebar_item_with_loader('Organizations', 'business', 'organizations'),
        ]

        await base.render(content, sidebar_items, use_dynamic_content=True)
