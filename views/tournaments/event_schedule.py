"""
Event Schedule View for tournaments.

Shows upcoming matches and events for the organization.
"""

from __future__ import annotations
import logging
from typing import Optional
from nicegui import ui
from models import Organization, User
from models.match_schedule import Match
from components.card import Card
from components.data_table import ResponsiveTable, TableColumn
from components.datetime_label import DateTimeLabel
from components.dialogs import MatchSeedDialog, EditMatchDialog
from application.services.tournament_service import TournamentService
from application.services.organization_service import OrganizationService
from application.services.authorization_service import AuthorizationService

logger = logging.getLogger(__name__)


class EventScheduleView:
    """View for displaying event schedule."""

    def __init__(self, organization: Organization, user: User) -> None:
        self.organization = organization
        self.user = user
        self.service = TournamentService()
        self.org_service = OrganizationService()
        self.auth_service = AuthorizationService()
        self.container = None
        self.filter_state = 'all'  # all, pending, scheduled, checked_in, in_progress, finished
        self.selected_tournaments = []  # List of selected tournament IDs
        self.can_manage_tournaments = False  # Set during render
        self.can_edit_matches = False  # Set during render (moderator or tournament admin)

    def _get_match_state(self, match: Match) -> str:
        """Get the state of a match."""
        if match.finished_at:
            return 'finished'
        elif match.started_at:
            return 'in_progress'
        elif match.checked_in_at:
            return 'checked_in'
        elif match.scheduled_at:
            return 'scheduled'
        else:
            return 'pending'

    def _filter_matches(self, matches):
        """Filter matches based on current filter state and selected tournaments."""
        filtered = []
        
        for match in matches:
            # Filter by state
            if self.filter_state != 'all':
                state = self._get_match_state(match)
                if state != self.filter_state:
                    continue
            
            # Filter by tournament selection
            if self.selected_tournaments and match.tournament_id not in self.selected_tournaments:
                continue
            
            filtered.append(match)
        
        return filtered

    async def _on_filter_change(self, new_state: str) -> None:
        """Handle filter state change."""
        self.filter_state = new_state
        await self._refresh()

    async def _on_tournament_filter_change(self, selected_ids) -> None:
        """Handle tournament filter change."""
        self.selected_tournaments = selected_ids if selected_ids else []
        await self._refresh()

    async def _refresh(self) -> None:
        """Refresh the view by clearing and re-rendering."""
        if self.container:
            self.container.clear()
            with self.container:
                await self._render_content()

    async def _render_content(self) -> None:
        """Render the actual content."""
        # Check if user can manage tournaments
        self.can_manage_tournaments = await self.org_service.user_can_manage_tournaments(
            self.user, self.organization.id
        )
        
        # Check if user can edit matches (tournament manager or moderator)
        self.can_edit_matches = self.can_manage_tournaments or self.auth_service.can_moderate(self.user)
        
        # Get all matches for this organization's tournaments via service
        all_matches = await self.service.list_org_matches(self.organization.id)
        
        # Get all tournaments for filter
        all_tournaments = await self.service.list_all_org_tournaments(self.organization.id)
        tournament_options = {t.id: t.name for t in all_tournaments}
        
        # Filter bar
        with ui.element('div').classes('card'):
            with ui.element('div').classes('card-body'):
                with ui.row().classes('full-width items-center gap-4 flex-wrap'):
                    ui.label('Filters:').classes('font-semibold')
                    
                    # Status filter
                    ui.select(
                        label='Status',
                        options={
                            'all': 'All Matches',
                            'pending': 'Pending',
                            'scheduled': 'Scheduled',
                            'checked_in': 'Checked In',
                            'in_progress': 'In Progress',
                            'finished': 'Finished'
                        },
                        value=self.filter_state,
                        on_change=lambda e: self._on_filter_change(e.value)
                    ).classes('min-w-[200px]')
                    
                    # Tournament filter (multi-select)
                    ui.select(
                        label='Tournaments',
                        options=tournament_options,
                        value=self.selected_tournaments,
                        multiple=True,
                        on_change=lambda e: self._on_tournament_filter_change(e.value)
                    ).classes('min-w-[200px]').props('use-chips')
        
        # Apply filter
        matches = self._filter_matches(all_matches)
        
        with Card.create(title=f'Event Schedule - {self.organization.name} ({len(matches)}/{len(all_matches)})'):
            if not matches:
                with ui.element('div').classes('text-center mt-4'):
                    ui.icon('event').classes('text-secondary icon-large')
                    ui.label('No upcoming events').classes('text-secondary')
                    ui.label('Check back later for scheduled matches').classes('text-secondary text-sm')
            else:
                def render_tournament(match: Match):
                    ui.label(match.tournament.name)
                
                def render_title(match: Match):
                    if match.title:
                        ui.label(match.title)
                    else:
                        ui.label('—').classes('text-secondary')
                
                def render_scheduled_time(match: Match):
                    if match.scheduled_at:
                        DateTimeLabel.datetime(match.scheduled_at)
                    else:
                        ui.label('TBD').classes('text-secondary')
                
                def render_stream(match: Match):
                    if match.stream_channel:
                        ui.label(match.stream_channel.name)
                    else:
                        ui.label('—').classes('text-secondary')
                
                def render_status(match: Match):
                    if match.finished_at:
                        ui.label('Finished').classes('badge badge-success')
                    elif match.started_at:
                        ui.label('In Progress').classes('badge badge-info')
                    elif match.checked_in_at:
                        ui.label('Checked In').classes('badge badge-warning')
                    elif match.scheduled_at:
                        ui.label('Scheduled').classes('badge badge-secondary')
                    else:
                        ui.label('Pending').classes('badge')
                
                async def signup_crew(match_id: int, role: str):
                    """Sign up for a crew role."""
                    try:
                        await self.service.signup_crew(
                            user=self.user,
                            organization_id=self.organization.id,
                            match_id=match_id,
                            role=role
                        )
                        ui.notify(f'Signed up as {role}', type='positive')
                        await self._refresh()
                    except Exception as e:
                        logger.error("Failed to sign up as crew: %s", e)
                        ui.notify(f'Failed to sign up: {str(e)}', type='negative')

                async def remove_crew(match_id: int, role: str):
                    """Remove crew signup."""
                    try:
                        result = await self.service.remove_crew_signup(
                            user=self.user,
                            organization_id=self.organization.id,
                            match_id=match_id,
                            role=role
                        )
                        if result:
                            ui.notify(f'Removed {role} signup', type='positive')
                            await self._refresh()
                        else:
                            ui.notify('Signup not found', type='warning')
                    except Exception as e:
                        logger.error("Failed to remove crew signup: %s", e)
                        ui.notify(f'Failed to remove signup: {str(e)}', type='negative')

                def render_commentator(match: Match):
                    """Render commentator(s) with approval status color and signup button."""
                    # Get crew members with commentator role
                    commentators = [
                        crew for crew in getattr(match, 'crew_members', [])
                        if crew.role.lower() == 'commentator'
                    ]
                    
                    # Check if current user is signed up
                    user_signed_up = any(crew.user_id == self.user.id for crew in commentators)
                    
                    with ui.column().classes('gap-2'):
                        if commentators:
                            with ui.column().classes('gap-1'):
                                for crew in commentators:
                                    # Green for approved, yellow for unapproved
                                    color_class = 'text-positive' if crew.approved else 'text-warning'
                                    ui.label(crew.user.discord_username).classes(color_class)
                        else:
                            ui.label('—').classes('text-secondary')
                        
                        # Sign up or remove button
                        if user_signed_up:
                            ui.button(
                                icon='remove_circle',
                                on_click=lambda m=match: remove_crew(m.id, 'commentator')
                            ).classes('btn btn-sm').props('flat color=negative size=sm').tooltip('Remove your commentator signup')
                        else:
                            ui.button(
                                icon='add_circle',
                                on_click=lambda m=match: signup_crew(m.id, 'commentator')
                            ).classes('btn btn-sm').props('flat color=positive size=sm').tooltip('Sign up as commentator')
                
                def render_tracker(match: Match):
                    """Render tracker(s) with approval status color and signup button."""
                    # Get crew members with tracker role
                    trackers = [
                        crew for crew in getattr(match, 'crew_members', [])
                        if crew.role.lower() == 'tracker'
                    ]
                    
                    # Check if tracker is enabled for this tournament
                    tracker_enabled = getattr(match.tournament, 'tracker_enabled', True)
                    
                    # Check if current user is signed up
                    user_signed_up = any(crew.user_id == self.user.id for crew in trackers)
                    
                    with ui.column().classes('gap-2'):
                        if trackers:
                            with ui.column().classes('gap-1'):
                                for crew in trackers:
                                    # Green for approved, yellow for unapproved
                                    color_class = 'text-positive' if crew.approved else 'text-warning'
                                    ui.label(crew.user.discord_username).classes(color_class)
                        else:
                            ui.label('—').classes('text-secondary')
                        
                        # Sign up or remove button (only if tracker enabled for this tournament)
                        if tracker_enabled:
                            if user_signed_up:
                                ui.button(
                                    icon='remove_circle',
                                    on_click=lambda m=match: remove_crew(m.id, 'tracker')
                                ).classes('btn btn-sm').props('flat color=negative size=sm').tooltip('Remove your tracker signup')
                            else:
                                ui.button(
                                    icon='add_circle',
                                    on_click=lambda m=match: signup_crew(m.id, 'tracker')
                                ).classes('btn btn-sm').props('flat color=positive size=sm').tooltip('Sign up as tracker')
                        else:
                            # Show disabled button with tooltip explaining why
                            ui.button(
                                icon='block',
                                on_click=None
                            ).classes('btn btn-sm').props('flat disable size=sm').tooltip('Tracker role not enabled for this tournament')
                
                async def open_seed_dialog(match_id: int, match_title: str):
                    """Open dialog to set/edit seed for a match."""
                    # Get current match to get seed info
                    match = next((m for m in matches if m.id == match_id), None)
                    if not match:
                        return
                    
                    seed = getattr(match, 'seed', None)
                    if seed and hasattr(seed, '__iter__') and not isinstance(seed, str):
                        seed_list = list(seed) if not isinstance(seed, list) else seed
                        seed = seed_list[0] if seed_list else None
                    
                    initial_url = seed.url if seed else ""
                    initial_description = seed.description if seed else None
                    
                    async def on_submit(url: str, description: Optional[str]):
                        await self.service.set_match_seed(
                            self.user, self.organization.id, match_id, url, description
                        )
                        ui.notify('Seed updated', type='positive')
                        await self._refresh()
                    
                    async def on_delete():
                        await self.service.delete_match_seed(
                            self.user, self.organization.id, match_id
                        )
                        ui.notify('Seed deleted', type='positive')
                        await self._refresh()
                    
                    dialog = MatchSeedDialog(
                        match_title=match_title or f'Match #{match_id}',
                        initial_url=initial_url,
                        initial_description=initial_description,
                        on_submit=on_submit,
                        on_delete=on_delete if seed else None,
                    )
                    await dialog.show()
                
                def render_seed(match: Match):
                    """Render seed/ROM link if available."""
                    # Check if seed exists (1:1 relationship)
                    seed = getattr(match, 'seed', None)
                    
                    # Handle the case where seed is a ReverseRelation (list)
                    if seed and hasattr(seed, '__iter__') and not isinstance(seed, str):
                        seed_list = list(seed) if not isinstance(seed, list) else seed
                        seed = seed_list[0] if seed_list else None
                    
                    with ui.column().classes('gap-2'):
                        if seed:
                            # Show link to seed URL
                            with ui.link(target=seed.url).classes('text-primary'):
                                with ui.row().classes('items-center gap-1'):
                                    ui.icon('file_download').classes('text-sm')
                                    ui.label('Seed')
                            # Show description if available
                            if seed.description:
                                ui.label(seed.description).classes('text-secondary text-xs')
                        else:
                            ui.label('—').classes('text-secondary')
                        
                        # Add "Set Seed" button for tournament managers
                        if self.can_manage_tournaments:
                            icon = 'edit' if seed else 'add'
                            tooltip = 'Edit seed' if seed else 'Set seed'
                            ui.button(
                                icon=icon,
                                on_click=lambda m=match: open_seed_dialog(m.id, m.title)
                            ).classes('btn btn-sm').props('flat color=primary size=sm').tooltip(tooltip)
                
                async def open_edit_match_dialog(match_id: int):
                    """Open dialog to edit a match."""
                    # Get current match
                    match = next((m for m in matches if m.id == match_id), None)
                    if not match:
                        return
                    
                    async def on_save(title: str, scheduled_at, stream_id, comment):
                        result = await self.service.update_match(
                            self.user,
                            self.organization.id,
                            match_id,
                            title=title,
                            scheduled_at=scheduled_at,
                            stream_channel_id=stream_id,
                            comment=comment,
                        )
                        if result:
                            ui.notify('Match updated', type='positive')
                            await self._refresh()
                        else:
                            ui.notify('Failed to update match', type='negative')
                    
                    dialog = EditMatchDialog(
                        match=match,
                        organization_id=self.organization.id,
                        on_save=on_save,
                    )
                    await dialog.show()
                
                def render_actions(match: Match):
                    """Render action buttons for moderators/tournament admins."""
                    if self.can_edit_matches:
                        with ui.row().classes('gap-1'):
                            ui.button(
                                icon='edit',
                                on_click=lambda m=match: open_edit_match_dialog(m.id)
                            ).classes('btn btn-sm').props('flat color=primary size=sm').tooltip('Edit match')
                    else:
                        ui.label('—').classes('text-secondary')
                
                columns = [
                    TableColumn('Tournament', cell_render=render_tournament),
                    TableColumn('Match', cell_render=render_title),
                    TableColumn('Scheduled', cell_render=render_scheduled_time),
                    TableColumn('Stream', cell_render=render_stream),
                    TableColumn('Seed', cell_render=render_seed),
                    TableColumn('Commentator', cell_render=render_commentator),
                    TableColumn('Tracker', cell_render=render_tracker),
                    TableColumn('Status', cell_render=render_status),
                    TableColumn('Actions', cell_render=render_actions),
                ]
                
                table = ResponsiveTable(columns, matches)
                await table.render()

    async def render(self) -> None:
        """Render the event schedule view."""
        self.container = ui.column().classes('w-full')
        with self.container:
            await self._render_content()
