"""
My Matches View for tournaments.

Shows matches the user is participating in.
"""

from __future__ import annotations
from nicegui import ui
from models import Organization, User
from models.match_schedule import MatchPlayers
from components.card import Card
from components.data_table import ResponsiveTable, TableColumn
from components.datetime_label import DateTimeLabel
from components.dialogs import SubmitMatchDialog
from application.services.tournament_service import TournamentService


class MyMatchesView:
    """View for displaying user's matches."""

    def __init__(self, organization: Organization, user: User) -> None:
        self.organization = organization
        self.user = user
        self.service = TournamentService()
        self.container = None
        self.filter_states = ['pending', 'scheduled', 'checked_in']  # Default: show pending, scheduled, checked_in
        self.selected_tournaments = []  # List of selected tournament IDs

    async def _refresh(self) -> None:
        """Refresh the view by clearing and re-rendering."""
        if self.container:
            self.container.clear()
            with self.container:
                await self._render_content()

    def _get_match_state(self, match) -> str:
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

    def _filter_matches(self, match_players):
        """Filter matches based on current filter states and selected tournaments."""
        if not self.filter_states and not self.selected_tournaments:
            return match_players
        
        filtered = []
        for mp in match_players:
            # Filter by state (if any states are selected)
            if self.filter_states:
                state = self._get_match_state(mp.match)
                if state not in self.filter_states:
                    continue
            
            # Filter by tournament selection
            if self.selected_tournaments and mp.match.tournament_id not in self.selected_tournaments:
                continue
            
            filtered.append(mp)
        return filtered

    async def _on_filter_change(self, new_states) -> None:
        """Handle filter state change."""
        self.filter_states = new_states if new_states else []
        await self._refresh()

    async def _on_tournament_filter_change(self, selected_ids) -> None:
        """Handle tournament filter change."""
        self.selected_tournaments = selected_ids if selected_ids else []
        await self._refresh()

    async def _render_content(self) -> None:
        """Render the actual content."""
        # Get all matches the user is participating in for this organization via service
        all_match_players = await self.service.list_user_matches(self.organization.id, self.user.id)
        
        # Get all tournaments for filter
        all_tournaments = await self.service.list_all_org_tournaments(self.organization.id)
        tournament_options = {t.id: t.name for t in all_tournaments}
        
        async def open_submit_match_dialog():
            """Open the submit match dialog."""
            dialog = SubmitMatchDialog(
                user=self.user,
                organization=self.organization,
                on_save=self._refresh
            )
            await dialog.show()
        
        # Action bar with submit button and filter
        with ui.element('div').classes('card'):
            with ui.element('div').classes('card-body'):
                with ui.row().classes('full-width items-center justify-between gap-4'):
                    # Filter dropdown (multi-select)
                    with ui.row().classes('items-center gap-4'):
                        ui.label('Filter:').classes('font-semibold')
                        ui.select(
                            label='Status',
                            options={
                                'pending': 'Pending',
                                'scheduled': 'Scheduled',
                                'checked_in': 'Checked In',
                                'in_progress': 'In Progress',
                                'finished': 'Finished'
                            },
                            value=self.filter_states,
                            multiple=True,
                            on_change=lambda e: self._on_filter_change(e.value)
                        ).classes('min-w-[200px]').props('use-chips')
                        
                        # Tournament filter (multi-select)
                        ui.select(
                            label='Tournaments',
                            options=tournament_options,
                            value=self.selected_tournaments,
                            multiple=True,
                            on_change=lambda e: self._on_tournament_filter_change(e.value)
                        ).classes('min-w-[200px]').props('use-chips')
                    
                    # Submit button
                    ui.button('Submit Match', icon='add', on_click=open_submit_match_dialog).classes('btn btn-primary')
        
        # Apply filter
        match_players = self._filter_matches(all_match_players)
        
        with Card.create(title=f'My Matches ({len(match_players)}/{len(all_match_players)})'):
            if not match_players:
                with ui.element('div').classes('text-center mt-4'):
                    ui.icon('sports_esports').classes('text-secondary icon-large')
                    ui.label('You have no matches scheduled').classes('text-secondary')
                    ui.label('Ask a tournament organizer to add you to a match').classes('text-secondary text-sm')
            else:
                def render_tournament(mp: MatchPlayers):
                    ui.label(mp.match.tournament.name)
                
                def render_match_title(mp: MatchPlayers):
                    if mp.match.title:
                        ui.label(mp.match.title)
                    else:
                        ui.label('Match')
                
                def render_scheduled_time(mp: MatchPlayers):
                    if mp.match.scheduled_at:
                        DateTimeLabel.datetime(mp.match.scheduled_at)
                    else:
                        ui.label('TBD').classes('text-secondary')
                
                def render_station(mp: MatchPlayers):
                    if mp.assigned_station:
                        ui.label(mp.assigned_station)
                    else:
                        ui.label('—').classes('text-secondary')
                
                def render_stream(mp: MatchPlayers):
                    if mp.match.stream_channel:
                        ui.label(mp.match.stream_channel.name)
                    else:
                        ui.label('—').classes('text-secondary')
                
                def render_opponents(mp: MatchPlayers):
                    """Render the other players in this match (excluding the current user)."""
                    all_players = getattr(mp.match, 'players', [])
                    opponents = [p for p in all_players if p.user_id != self.user.id]
                    
                    if opponents:
                        with ui.column().classes('gap-1'):
                            for opponent in opponents:
                                ui.label(opponent.user.discord_username).classes('text-sm')
                    else:
                        ui.label('—').classes('text-secondary')
                
                def render_status(mp: MatchPlayers):
                    match = mp.match
                    if match.finished_at:
                        if mp.finish_rank == 1:
                            ui.label('Won').classes('badge badge-success')
                        elif mp.finish_rank:
                            ui.label(f'Place {mp.finish_rank}').classes('badge')
                        else:
                            ui.label('Finished').classes('badge badge-success')
                    elif match.started_at:
                        ui.label('In Progress').classes('badge badge-info')
                    elif match.checked_in_at:
                        ui.label('Checked In').classes('badge badge-warning')
                    elif match.scheduled_at:
                        ui.label('Scheduled').classes('badge badge-secondary')
                    else:
                        ui.label('Pending').classes('badge')
                
                columns = [
                    TableColumn('Tournament', cell_render=render_tournament),
                    TableColumn('Match', cell_render=render_match_title),
                    TableColumn('Opponents', cell_render=render_opponents),
                    TableColumn('Scheduled', cell_render=render_scheduled_time),
                    TableColumn('Station', cell_render=render_station),
                    TableColumn('Stream', cell_render=render_stream),
                    TableColumn('Status', cell_render=render_status),
                ]
                
                table = ResponsiveTable(columns, match_players)
                await table.render()

    async def render(self) -> None:
        """Render the my matches view."""
        self.container = ui.column().classes('w-full')
        with self.container:
            await self._render_content()
