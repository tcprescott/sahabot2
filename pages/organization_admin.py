"""
Organization-specific admin page.

Accessible by SUPERADMIN/ADMIN or members with an org-level admin role.
"""

from __future__ import annotations
from nicegui import ui
from components.base_page import BasePage
from application.services.organization_service import OrganizationService
from views.organization import (
    OrganizationOverviewView,
    OrganizationMembersView,
    OrganizationPermissionsView,
    OrganizationSettingsView,
)


def register():
    """Register organization admin route."""

    @ui.page('/admin/organizations/{organization_id}')
    async def organization_admin_page(organization_id: int):
        """Organization admin page with scoped authorization checks."""
        base = BasePage.authenticated_page(title="Organization Admin")
        service = OrganizationService()

        async def content(page: BasePage):
            # Authorization: allow global admins or org-admin members
            allowed = await service.user_can_admin_org(page.user, organization_id)
            if not allowed:
                ui.notify('You do not have access to administer this organization.', color='negative')
                ui.navigate.to('/admin')
                return

            org = await service.get_organization(organization_id)
            if not org:
                with ui.element('div').classes('card'):
                    with ui.element('div').classes('card-header'):
                        ui.label('Organization not found')
                    with ui.element('div').classes('card-body'):
                        ui.button('Back to Admin', on_click=lambda: ui.navigate.to('/admin')).classes('btn')
                return

            # Register content loaders for different sections
            async def load_overview():
                """Load organization overview."""
                container = page.get_dynamic_content_container()
                if container:
                    container.clear()
                    with container:
                        view = OrganizationOverviewView(org, page.user)
                        await view.render()

            async def load_members():
                """Load members management."""
                container = page.get_dynamic_content_container()
                if container:
                    container.clear()
                    with container:
                        view = OrganizationMembersView(org, page.user)
                        await view.render()

            async def load_permissions():
                """Load permissions management."""
                container = page.get_dynamic_content_container()
                if container:
                    container.clear()
                    with container:
                        view = OrganizationPermissionsView(org, page.user)
                        await view.render()

            async def load_settings():
                """Load organization settings."""
                container = page.get_dynamic_content_container()
                if container:
                    container.clear()
                    with container:
                        view = OrganizationSettingsView(org, page.user)
                        await view.render()

            # Register loaders
            page.register_content_loader('overview', load_overview)
            page.register_content_loader('members', load_members)
            page.register_content_loader('permissions', load_permissions)
            page.register_content_loader('settings', load_settings)

            # Load initial content (overview)
            await load_overview()

        # Create sidebar items
        sidebar_items = [
            base.create_nav_link('Back to Admin', 'arrow_back', '/admin'),
            base.create_separator(),
            base.create_sidebar_item_with_loader('Overview', 'dashboard', 'overview'),
            base.create_sidebar_item_with_loader('Members', 'people', 'members'),
            base.create_sidebar_item_with_loader('Permissions', 'verified_user', 'permissions'),
            base.create_sidebar_item_with_loader('Settings', 'settings', 'settings'),
        ]

        await base.render(content, sidebar_items, use_dynamic_content=True)
