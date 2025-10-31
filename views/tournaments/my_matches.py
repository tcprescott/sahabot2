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
from application.services.tournament_service import TournamentService


class MyMatchesView:
    """View for displaying user's matches."""

    def __init__(self, organization: Organization, user: User) -> None:
        self.organization = organization
        self.user = user
        self.service = TournamentService()

    async def render(self) -> None:
        """Render the my matches view."""
        # Get all matches the user is participating in for this organization via service
        match_players = await self.service.list_user_matches(self.organization.id, self.user.id)
        
        with Card.create(title='My Matches'):
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
                        ui.label(mp.match.scheduled_at.strftime('%Y-%m-%d %H:%M'))
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
                    TableColumn('Scheduled', cell_render=render_scheduled_time),
                    TableColumn('Station', cell_render=render_station),
                    TableColumn('Stream', cell_render=render_stream),
                    TableColumn('Status', cell_render=render_status),
                ]
                
                table = ResponsiveTable(columns, match_players)
                await table.render()
