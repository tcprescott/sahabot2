"""
Tournaments page.

Shows organization selector, then organization-scoped tournament views.
"""

from __future__ import annotations
from nicegui import ui
from components.base_page import BasePage
from application.services.organization_service import OrganizationService
from application.services.tournament_service import TournamentService
from application.services.tournament_usage_service import TournamentUsageService
from models import OrganizationMember
from models.async_tournament import AsyncTournament
from models.match_schedule import Tournament
from views.tournaments import (
    TournamentOrgSelectView,
    EventScheduleView,
    MyMatchesView,
    MySettingsView,
    TournamentManagementView,
    AsyncDashboardView,
    AsyncLeaderboardView,
    AsyncPoolsView,
    AsyncPlayerHistoryView,
    AsyncPermalinkView,
    AsyncReviewQueueView,
)
from views.organization import (
    OrganizationOverviewView,
)


def register():
    """Register tournament page routes."""

    @ui.page('/org')
    async def tournaments_page():
        """Organization features page - show organization selector."""
        base = BasePage.authenticated_page(title="Organizations")

        async def content(page: BasePage):
            """Render organization selection page."""
            view = TournamentOrgSelectView(page.user)
            await view.render()

        # Create sidebar items
        sidebar_items = [
            base.create_nav_link('Back to Home', 'home', '/'),
        ]

        await base.render(content, sidebar_items)

    @ui.page('/org/{organization_id}')
    async def organization_page(organization_id: int):
        """Organization page - show organization features and members."""
        base = BasePage.authenticated_page(title="Organization")
        org_service = OrganizationService()

        # Pre-check that user is a member of the organization
        from middleware.auth import DiscordAuthService
        user = await DiscordAuthService.get_current_user()
        
        # Check if user is a member of this organization
        member = await OrganizationMember.filter(user_id=user.id, organization_id=organization_id).first()
        is_member = member is not None
        
        # Check if user can access admin panel
        can_admin = await org_service.user_can_admin_org(user, organization_id)
        can_manage_tournaments = await org_service.user_can_manage_tournaments(user, organization_id)
        can_access_admin = can_admin or can_manage_tournaments
        
        # Get active tournaments for sidebar
        active_async_tournaments = await AsyncTournament.filter(
            organization_id=organization_id,
            is_active=True
        ).all()
        
        active_tournaments = await Tournament.filter(
            organization_id=organization_id,
            is_active=True
        ).all()
        
        async def content(page: BasePage):
            # Re-check membership inside content
            if not is_member:
                ui.notify('You must be a member of this organization to view organization features.', color='negative')
                ui.navigate.to('/org')
                return

            org = await org_service.get_organization(organization_id)
            if not org:
                with ui.element('div').classes('card'):
                    with ui.element('div').classes('card-header'):
                        ui.label('Organization not found')
                    with ui.element('div').classes('card-body'):
                        ui.button('Back to Organizations', on_click=lambda: ui.navigate.to('/org')).classes('btn')
                return

            # Register content loaders for different sections
            async def load_overview():
                """Load overview view."""
                container = page.get_dynamic_content_container()
                if container:
                    container.clear()
                    with container:
                        view = OrganizationOverviewView(org, page.user)
                        await view.render()

            # Register loaders
            page.register_content_loader('overview', load_overview)

            # Load initial content
            await load_overview()

        # Create sidebar items
        sidebar_items = [
            base.create_nav_link('Back to Organizations', 'arrow_back', '/org'),
            base.create_separator(),
            base.create_sidebar_item_with_loader('Overview', 'dashboard', 'overview'),
            base.create_nav_link('Tournaments', 'emoji_events', f'/org/{organization_id}/tournament'),
            base.create_nav_link('Async Tournaments', 'schedule', f'/org/{organization_id}/async'),
        ]
        
        # Add admin link if user has permissions
        if can_access_admin:
            sidebar_items.append(base.create_separator())
            sidebar_items.append(
                base.create_nav_link('Administration', 'admin_panel_settings', f'/orgs/{organization_id}/admin')
            )
        
        # Add active tournament links if there are any
        if active_tournaments or active_async_tournaments:
            sidebar_items.append(base.create_separator())
            
            # Add regular tournaments
            for tournament in active_tournaments:
                sidebar_items.append(
                    base.create_nav_link(
                        f'🏆 {tournament.name}',
                        'emoji_events',
                        f'/org/{organization_id}/tournament?tournament_id={tournament.id}'
                    )
                )
            
            # Add async tournaments
            for tournament in active_async_tournaments:
                sidebar_items.append(
                    base.create_nav_link(
                        f'🏁 {tournament.name}',
                        'schedule',
                        f'/org/{organization_id}/async/{tournament.id}'
                    )
                )

        await base.render(content, sidebar_items, use_dynamic_content=True)

    @ui.page('/org/{organization_id}/async')
    @ui.page('/org/{organization_id}/async')
    async def async_tournament_overview_page(organization_id: int):
        """Async tournaments overview page for an organization."""
        base = BasePage.authenticated_page(title="Async Tournaments")
        org_service = OrganizationService()

        # Pre-check that user is a member of the organization
        from middleware.auth import DiscordAuthService
        user = await DiscordAuthService.get_current_user()
        
        # Check if user is a member of this organization
        member = await OrganizationMember.filter(user_id=user.id, organization_id=organization_id).first()
        is_member = member is not None
        
        # Get active tournaments for sidebar
        active_async_tournaments = await AsyncTournament.filter(
            organization_id=organization_id,
            is_active=True
        ).all()
        
        active_tournaments = await Tournament.filter(
            organization_id=organization_id,
            is_active=True
        ).all()
        
        async def content(_page: BasePage):
            # Re-check membership inside content
            if not is_member:
                ui.notify('You must be a member of this organization to view organization features.', color='negative')
                ui.navigate.to('/org')
                return

            org = await org_service.get_organization(organization_id)
            if not org:
                with ui.element('div').classes('card'):
                    with ui.element('div').classes('card-header'):
                        ui.label('Organization not found')
                    with ui.element('div').classes('card-body'):
                        ui.button('Back to Organizations', on_click=lambda: ui.navigate.to('/org')).classes('btn')
                return

            # Get all async tournaments for this organization
            all_tournaments = await AsyncTournament.filter(organization_id=organization_id).order_by('-created_at').all()
            active = [t for t in all_tournaments if t.is_active]
            inactive = [t for t in all_tournaments if not t.is_active]
            
            from components.card import Card
            from components.datetime_label import DateTimeLabel
            
            # Header
            with Card.create(title='Async Tournaments'):
                with ui.column().classes('gap-md'):
                    ui.label(f'View and participate in async tournaments for {org.name}').classes('text-secondary')
                    
                    if active:
                        ui.separator()
                        ui.label('Active Tournaments').classes('text-lg font-semibold')
                        with ui.column().classes('gap-sm'):
                            for tournament in active:
                                with ui.element('div').classes('card'):
                                    with ui.element('div').classes('card-body'):
                                        with ui.row().classes('w-full items-center justify-between'):
                                            with ui.column().classes('gap-1'):
                                                ui.link(
                                                    tournament.name,
                                                    f'/org/{organization_id}/async/{tournament.id}'
                                                ).classes('text-xl font-semibold')
                                                if tournament.description:
                                                    ui.label(tournament.description).classes('text-secondary text-sm')
                                                with ui.row().classes('gap-md items-center'):
                                                    ui.label('Created:').classes('text-sm text-secondary')
                                                    DateTimeLabel.datetime(tournament.created_at)
                                            with ui.column().classes('items-end gap-1'):
                                                ui.label('Active').classes('badge badge-success')
                                                ui.button(
                                                    'View Dashboard',
                                                    icon='arrow_forward',
                                                    on_click=lambda t=tournament: ui.navigate.to(f'/org/{organization_id}/async/{t.id}')
                                                ).classes('btn btn-primary')
                    
                    if inactive:
                        ui.separator()
                        ui.label('Past Tournaments').classes('text-lg font-semibold')
                        with ui.column().classes('gap-sm'):
                            for tournament in inactive:
                                with ui.element('div').classes('card'):
                                    with ui.element('div').classes('card-body'):
                                        with ui.row().classes('w-full items-center justify-between'):
                                            with ui.column().classes('gap-1'):
                                                ui.link(
                                                    tournament.name,
                                                    f'/org/{organization_id}/async/{tournament.id}'
                                                ).classes('text-xl font-semibold')
                                                if tournament.description:
                                                    ui.label(tournament.description).classes('text-secondary text-sm')
                                                with ui.row().classes('gap-md items-center'):
                                                    ui.label('Created:').classes('text-sm text-secondary')
                                                    DateTimeLabel.datetime(tournament.created_at)
                                            with ui.column().classes('items-end gap-1'):
                                                ui.label('Closed').classes('badge badge-danger')
                                                ui.button(
                                                    'View Results',
                                                    icon='arrow_forward',
                                                    on_click=lambda t=tournament: ui.navigate.to(f'/org/{organization_id}/async/{t.id}')
                                                ).classes('btn')
                    
                    if not all_tournaments:
                        with ui.element('div').classes('text-center mt-4'):
                            ui.icon('schedule').classes('text-secondary icon-large')
                            ui.label('No async tournaments yet').classes('text-secondary')
                            ui.label('Ask an administrator to create one').classes('text-secondary text-sm')

        # Create sidebar items (same as organization overview)
        sidebar_items = [
            base.create_nav_link('Back to Organization', 'arrow_back', f'/org/{organization_id}'),
            base.create_separator(),
        ]
        
        # Add active tournament links if there are any
        if active_tournaments or active_async_tournaments:
            # Add regular tournaments
            for tournament in active_tournaments:
                sidebar_items.append(
                    base.create_nav_link(
                        f'🏆 {tournament.name}',
                        'emoji_events',
                        f'/org/{organization_id}/tournament?tournament_id={tournament.id}'
                    )
                )
            
            # Add async tournaments
            for tournament in active_async_tournaments:
                sidebar_items.append(
                    base.create_nav_link(
                        f'🏁 {tournament.name}',
                        'schedule',
                        f'/org/{organization_id}/async/{tournament.id}'
                    )
                )

        await base.render(content, sidebar_items)

    @ui.page('/org/{organization_id}/tournament')
    async def tournament_org_page(organization_id: int, tournament_id: int | None = None):
        """Organization features page for specific organization."""
        base = BasePage.authenticated_page(title="Organization")
        org_service = OrganizationService()
        tournament_service = TournamentService()
        usage_service = TournamentUsageService()

        # Pre-check that user is a member of the organization
        from middleware.auth import DiscordAuthService
        user = await DiscordAuthService.get_current_user()
        
        # Check if user is a member of this organization
        member = await OrganizationMember.filter(user_id=user.id, organization_id=organization_id).first()
        is_member = member is not None
        
        # Track tournament usage if tournament_id is provided
        if is_member and tournament_id:
            tournament = await Tournament.filter(id=tournament_id, organization_id=organization_id).first()
            if tournament:
                org = await org_service.get_organization(organization_id)
                if org:
                    await usage_service.track_tournament_access(
                        user=user,
                        tournament=tournament,
                        organization_id=organization_id,
                        organization_name=org.name,
                    )
        
        async def content(page: BasePage):
            # Re-check membership inside content
            if not is_member:
                ui.notify('You must be a member of this organization to view organization features.', color='negative')
                ui.navigate.to('/org')
                return

            org = await org_service.get_organization(organization_id)
            if not org:
                with ui.element('div').classes('card'):
                    with ui.element('div').classes('card-header'):
                        ui.label('Organization not found')
                    with ui.element('div').classes('card-body'):
                        ui.button('Back to Organizations', on_click=lambda: ui.navigate.to('/org')).classes('btn')
                return

            # Register content loaders for different sections
            async def load_event_schedule():
                """Load event schedule."""
                container = page.get_dynamic_content_container()
                if container:
                    container.clear()
                    with container:
                        view = EventScheduleView(org, page.user)
                        if tournament_id:
                            view.selected_tournaments = [tournament_id]
                        await view.render()

            async def load_my_matches():
                """Load my matches."""
                container = page.get_dynamic_content_container()
                if container:
                    container.clear()
                    with container:
                        view = MyMatchesView(org, page.user)
                        if tournament_id:
                            view.selected_tournaments = [tournament_id]
                        await view.render()

            async def load_my_settings():
                """Load my settings."""
                container = page.get_dynamic_content_container()
                if container:
                    container.clear()
                    with container:
                        view = MySettingsView(page.user, org, tournament_service)
                        await view.render()

            async def load_tournament_management():
                """Load tournament management."""
                container = page.get_dynamic_content_container()
                if container:
                    container.clear()
                    with container:
                        view = TournamentManagementView(org, page.user)
                        if tournament_id:
                            view.selected_tournaments = [tournament_id]
                        await view.render()

            # Register loaders
            page.register_content_loader('event_schedule', load_event_schedule)
            page.register_content_loader('my_matches', load_my_matches)
            page.register_content_loader('my_settings', load_my_settings)
            page.register_content_loader('tournament_management', load_tournament_management)

            # Load initial content
            await load_event_schedule()

        # Create sidebar items
        sidebar_items = [
            base.create_nav_link('Back to Organization', 'arrow_back', f'/org/{organization_id}'),
            base.create_separator(),
            base.create_sidebar_item_with_loader('Event Schedule', 'event', 'event_schedule'),
            base.create_sidebar_item_with_loader('My Matches', 'sports_esports', 'my_matches'),
            base.create_sidebar_item_with_loader('My Settings', 'settings', 'my_settings'),
            base.create_separator(),
            base.create_sidebar_item_with_loader('Tournament Management', 'admin_panel_settings', 'tournament_management'),
        ]

        await base.render(content, sidebar_items, use_dynamic_content=True)

    # Async Tournament Pages

    @ui.page('/org/{organization_id}/async/{tournament_id}')
    async def async_tournament_dashboard(organization_id: int, tournament_id: int):
        """Async tournament dashboard - player's own races."""
        base = BasePage.authenticated_page(title="Async Tournament")
        
        from application.services.async_tournament_service import AsyncTournamentService
        async_service = AsyncTournamentService()

        async def content(page: BasePage):
            # Get tournament
            tournament = await async_service.get_tournament(page.user, organization_id, tournament_id)
            if not tournament:
                ui.label('Tournament not found or you do not have access').classes('text-danger')
                return

            view = AsyncDashboardView(page.user, tournament)
            await view.render()

        sidebar_items = [
            base.create_nav_link('Back to Organization', 'arrow_back', f'/org/{organization_id}'),
        ]

        await base.render(content, sidebar_items)

    @ui.page('/org/{organization_id}/async/{tournament_id}/leaderboard')
    async def async_tournament_leaderboard(organization_id: int, tournament_id: int):
        """Async tournament leaderboard."""
        base = BasePage.authenticated_page(title="Async Tournament Leaderboard")
        
        from application.services.async_tournament_service import AsyncTournamentService
        async_service = AsyncTournamentService()

        async def content(page: BasePage):
            # Get tournament
            tournament = await async_service.get_tournament(page.user, organization_id, tournament_id)
            if not tournament:
                ui.label('Tournament not found or you do not have access').classes('text-danger')
                return

            view = AsyncLeaderboardView(page.user, tournament)
            await view.render()

        sidebar_items = [
            base.create_nav_link('Dashboard', 'dashboard', f'/org/{organization_id}/async/{tournament_id}'),
            base.create_nav_link('Leaderboard', 'leaderboard', f'/org/{organization_id}/async/{tournament_id}/leaderboard'),
            base.create_nav_link('Pools', 'folder', f'/org/{organization_id}/async/{tournament_id}/pools'),
        ]

        await base.render(content, sidebar_items)

    @ui.page('/org/{organization_id}/async/{tournament_id}/pools')
    async def async_tournament_pools(organization_id: int, tournament_id: int):
        """Async tournament pools."""
        base = BasePage.authenticated_page(title="Async Tournament Pools")
        
        from application.services.async_tournament_service import AsyncTournamentService
        async_service = AsyncTournamentService()

        async def content(page: BasePage):
            # Get tournament
            tournament = await async_service.get_tournament(page.user, organization_id, tournament_id)
            if not tournament:
                ui.label('Tournament not found or you do not have access').classes('text-danger')
                return

            view = AsyncPoolsView(page.user, tournament)
            await view.render()

        sidebar_items = [
            base.create_nav_link('Dashboard', 'dashboard', f'/org/{organization_id}/async/{tournament_id}'),
            base.create_nav_link('Leaderboard', 'leaderboard', f'/org/{organization_id}/async/{tournament_id}/leaderboard'),
            base.create_nav_link('Pools', 'folder', f'/org/{organization_id}/async/{tournament_id}/pools'),
        ]

        await base.render(content, sidebar_items)

    @ui.page('/org/{organization_id}/async/{tournament_id}/player/{player_id}')
    async def async_tournament_player(organization_id: int, tournament_id: int, player_id: int):
        """Async tournament player history."""
        base = BasePage.authenticated_page(title="Player History")
        
        from application.services.async_tournament_service import AsyncTournamentService
        async_service = AsyncTournamentService()

        async def content(page: BasePage):
            # Get tournament
            tournament = await async_service.get_tournament(page.user, organization_id, tournament_id)
            if not tournament:
                ui.label('Tournament not found or you do not have access').classes('text-danger')
                return

            view = AsyncPlayerHistoryView(page.user, tournament, player_id)
            await view.render()

        sidebar_items = [
            base.create_nav_link('Dashboard', 'dashboard', f'/org/{organization_id}/async/{tournament_id}'),
            base.create_nav_link('Leaderboard', 'leaderboard', f'/org/{organization_id}/async/{tournament_id}/leaderboard'),
        ]

        await base.render(content, sidebar_items)

    @ui.page('/org/{organization_id}/async/{tournament_id}/permalink/{permalink_id}')
    async def async_tournament_permalink(organization_id: int, tournament_id: int, permalink_id: int):
        """Async tournament permalink view."""
        base = BasePage.authenticated_page(title="Permalink Races")
        
        from application.services.async_tournament_service import AsyncTournamentService
        async_service = AsyncTournamentService()

        async def content(page: BasePage):
            # Get tournament
            tournament = await async_service.get_tournament(page.user, organization_id, tournament_id)
            if not tournament:
                ui.label('Tournament not found or you do not have access').classes('text-danger')
                return

            view = AsyncPermalinkView(page.user, tournament, permalink_id)
            await view.render()

        sidebar_items = [
            base.create_nav_link('Dashboard', 'dashboard', f'/org/{organization_id}/async/{tournament_id}'),
            base.create_nav_link('Leaderboard', 'leaderboard', f'/org/{organization_id}/async/{tournament_id}/leaderboard'),
            base.create_nav_link('Pools', 'folder', f'/org/{organization_id}/async/{tournament_id}/pools'),
        ]

        await base.render(content, sidebar_items)

    @ui.page('/org/{organization_id}/async/{tournament_id}/review')
    async def async_tournament_review_queue(organization_id: int, tournament_id: int):
        """Async tournament review queue - for reviewers only."""
        base = BasePage.authenticated_page(title="Race Review Queue")

        from application.services.async_tournament_service import AsyncTournamentService
        async_service = AsyncTournamentService()

        async def content(page: BasePage):
            # Get tournament
            tournament = await async_service.get_tournament(page.user, organization_id, tournament_id)
            if not tournament:
                ui.label('Tournament not found or you do not have access').classes('text-danger')
                return

            # Check if user has review permissions
            can_review = await async_service.can_review_async_races(page.user, organization_id)
            if not can_review:
                ui.label('You do not have permission to review races').classes('text-danger')
                return

            view = AsyncReviewQueueView(tournament, page.user, organization_id)
            await view.render()

        sidebar_items = [
            base.create_nav_link('Dashboard', 'dashboard', f'/org/{organization_id}/async/{tournament_id}'),
            base.create_nav_link('Leaderboard', 'leaderboard', f'/org/{organization_id}/async/{tournament_id}/leaderboard'),
            base.create_nav_link('Pools', 'folder', f'/org/{organization_id}/async/{tournament_id}/pools'),
            base.create_separator(),
            base.create_nav_link('Review Queue', 'rate_review', f'/org/{organization_id}/async/{tournament_id}/review'),
        ]

        await base.render(content, sidebar_items)
