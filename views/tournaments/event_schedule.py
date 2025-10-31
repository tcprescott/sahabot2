"""
Event Schedule View for tournaments.

Shows upcoming matches and events for the organization.
"""

from __future__ import annotations
from nicegui import ui
from models import Organization, User
from models.match_schedule import Match
from components.card import Card
from components.data_table import ResponsiveTable, TableColumn
from application.services.tournament_service import TournamentService


class EventScheduleView:
    """View for displaying event schedule."""

    def __init__(self, organization: Organization, user: User) -> None:
        self.organization = organization
        self.user = user
        self.service = TournamentService()

    async def render(self) -> None:
        """Render the event schedule view."""
        # Get all matches for this organization's tournaments via service
        matches = await self.service.list_org_matches(self.organization.id)
        
        with Card.create(title=f'Event Schedule - {self.organization.name}'):
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
                        ui.label(match.scheduled_at.strftime('%Y-%m-%d %H:%M'))
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
                
                columns = [
                    TableColumn('Tournament', cell_render=render_tournament),
                    TableColumn('Match', cell_render=render_title),
                    TableColumn('Scheduled', cell_render=render_scheduled_time),
                    TableColumn('Stream', cell_render=render_stream),
                    TableColumn('Status', cell_render=render_status),
                ]
                
                table = ResponsiveTable(columns, matches)
                await table.render()
