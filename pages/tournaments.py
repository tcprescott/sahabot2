"""
Tournaments page.

Shows organization selector, then organization-scoped tournament views.
"""

from __future__ import annotations
from nicegui import ui
from components.base_page import BasePage
from application.services.organization_service import OrganizationService
from views.tournaments import (
    TournamentOrgSelectView,
    EventScheduleView,
    MyMatchesView,
    MySettingsView,
)


def register():
    """Register tournament page routes."""

    @ui.page('/tournaments')
    async def tournaments_page():
        """Tournament page - show organization selector."""
        base = BasePage.authenticated_page(title="Tournaments", active_nav="tournaments")

        async def content(page: BasePage):
            """Render organization selection page."""
            view = TournamentOrgSelectView(page.user)
            await view.render()

        await base.render(content)

    @ui.page('/tournaments/{organization_id}')
    async def tournament_org_page(organization_id: int):
        """Tournament page for specific organization."""
        base = BasePage.authenticated_page(title="Tournaments")
        service = OrganizationService()

        # Pre-check that user is a member of the organization
        from middleware.auth import DiscordAuthService
        user = await DiscordAuthService.get_current_user()
        
        # Check if user is a member of this organization
        is_member = await service.is_user_member(user.id, organization_id)
        
        async def content(page: BasePage):
            # Re-check membership inside content
            if not is_member:
                ui.notify('You must be a member of this organization to view tournaments.', color='negative')
                ui.navigate.to('/tournaments')
                return

            org = await service.get_organization(organization_id)
            if not org:
                with ui.element('div').classes('card'):
                    with ui.element('div').classes('card-header'):
                        ui.label('Organization not found')
                    with ui.element('div').classes('card-body'):
                        ui.button('Back to Tournaments', on_click=lambda: ui.navigate.to('/tournaments')).classes('btn')
                return

            # Register content loaders for different sections
            async def load_event_schedule():
                """Load event schedule."""
                container = page.get_dynamic_content_container()
                if container:
                    container.clear()
                    with container:
                        view = EventScheduleView(org, page.user)
                        await view.render()

            async def load_my_matches():
                """Load my matches."""
                container = page.get_dynamic_content_container()
                if container:
                    container.clear()
                    with container:
                        view = MyMatchesView(org, page.user)
                        await view.render()

            async def load_my_settings():
                """Load my settings."""
                container = page.get_dynamic_content_container()
                if container:
                    container.clear()
                    with container:
                        view = MySettingsView(org, page.user)
                        await view.render()

            # Register loaders
            page.register_content_loader('event_schedule', load_event_schedule)
            page.register_content_loader('my_matches', load_my_matches)
            page.register_content_loader('my_settings', load_my_settings)

            # Load initial content
            await load_event_schedule()

        # Create sidebar items
        sidebar_items = [
            base.create_nav_link('Back to Organizations', 'arrow_back', '/tournaments'),
            base.create_separator(),
            base.create_sidebar_item_with_loader('Event Schedule', 'event', 'event_schedule'),
            base.create_sidebar_item_with_loader('My Matches', 'sports_esports', 'my_matches'),
            base.create_sidebar_item_with_loader('My Settings', 'settings', 'my_settings'),
        ]

        await base.render(content, sidebar_items, use_dynamic_content=True)
