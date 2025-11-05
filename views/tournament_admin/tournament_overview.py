"""
Tournament Overview View.

Shows tournament dashboard with stats and quick actions.
"""

from __future__ import annotations
from nicegui import ui
from models import User
from models.organizations import Organization
from models.async_tournament import AsyncTournament
from models.audit_log import AuditLog
from components.datetime_label import DateTimeLabel


class TournamentOverviewView:
    """View for tournament overview dashboard."""

    def __init__(self, user: User, organization: Organization, tournament: AsyncTournament):
        """
        Initialize the overview view.

        Args:
            user: Current user
            organization: Tournament's organization
            tournament: Tournament to display
        """
        self.user = user
        self.organization = organization
        self.tournament = tournament

    async def render(self):
        """Render the tournament overview."""
        with ui.element('div').classes('card'):
            with ui.element('div').classes('card-header'):
                ui.label('Tournament Overview').classes('text-xl font-bold')

            with ui.element('div').classes('card-body'):
                # Tournament info
                with ui.row().classes('gap-4 mb-4'):
                    with ui.column().classes('flex-1'):
                        ui.label('Name:').classes('font-bold')
                        ui.label(self.tournament.name)

                    with ui.column().classes('flex-1'):
                        ui.label('Status:').classes('font-bold')
                        status_text = 'Active' if self.tournament.is_active else 'Inactive'
                        ui.label(status_text)

                ui.separator()

                # Description
                ui.label('Description:').classes('font-bold mt-4 mb-2')
                ui.label(self.tournament.description or 'No description provided').classes('text-sm')

                ui.separator()

                # Quick stats (placeholders for future implementation)
                ui.label('Quick Stats').classes('text-lg font-bold mt-4 mb-2')
                with ui.row().classes('gap-4'):
                    with ui.element('div').classes('card flex-1'):
                        with ui.element('div').classes('card-body text-center'):
                            ui.label('0').classes('text-3xl font-bold')
                            ui.label('Total Matches').classes('text-sm text-grey')

                    with ui.element('div').classes('card flex-1'):
                        with ui.element('div').classes('card-body text-center'):
                            ui.label('0').classes('text-3xl font-bold')
                            ui.label('Active Players').classes('text-sm text-grey')

                    with ui.element('div').classes('card flex-1'):
                        with ui.element('div').classes('card-body text-center'):
                            ui.label('0').classes('text-3xl font-bold')
                            ui.label('Completed Races').classes('text-sm text-grey')

        # SpeedGaming Integration section (if enabled)
        if self.tournament.speedgaming_enabled:
            await self._render_speedgaming_sync_section()

    async def _render_speedgaming_sync_section(self):
        """Render SpeedGaming sync information section."""
        with ui.element('div').classes('card mt-4'):
            with ui.element('div').classes('card-header'):
                with ui.row().classes('items-center justify-between w-full'):
                    ui.label('SpeedGaming Integration').classes('text-xl font-bold')
                    ui.badge('Active').classes('badge-success')

            with ui.element('div').classes('card-body'):
                # Integration info
                with ui.row().classes('gap-4 mb-4'):
                    with ui.column().classes('flex-1'):
                        ui.label('Event Slug:').classes('font-bold')
                        ui.label(self.tournament.speedgaming_event_slug or 'Not configured').classes('text-sm')

                    with ui.column().classes('flex-1'):
                        ui.label('Sync Frequency:').classes('font-bold')
                        ui.label('Every 5 minutes').classes('text-sm')

                ui.separator().classes('my-4')

                # Sync History
                ui.label('Recent Sync Activity').classes('text-lg font-bold mb-2')

                # Fetch recent sync logs
                # Note: Using JSON field filter for tournament_id. Consider adding
                # a direct tournament_id field to AuditLog if performance becomes an issue.
                sync_logs = await AuditLog.filter(
                    action="speedgaming_sync",
                    details__tournament_id=self.tournament.id,
                    organization_id=self.organization.id
                ).order_by('-created_at').limit(10).all()

                if not sync_logs:
                    with ui.element('div').classes('text-center py-4'):
                        ui.icon('sync').classes('text-secondary icon-large')
                        ui.label('No sync activity yet').classes('text-secondary')
                        ui.label('The next sync will occur within 5 minutes').classes('text-secondary text-sm')
                else:
                    # Display sync history table
                    with ui.element('div').classes('overflow-x-auto'):
                        with ui.element('table').classes('data-table'):
                            # Header
                            with ui.element('thead'):
                                with ui.element('tr'):
                                    ui.element('th').classes('text-left').add(ui.label('Time'))
                                    ui.element('th').classes('text-left').add(ui.label('Status'))
                                    ui.element('th').classes('text-center').add(ui.label('Imported'))
                                    ui.element('th').classes('text-center').add(ui.label('Updated'))
                                    ui.element('th').classes('text-center').add(ui.label('Deleted'))
                                    ui.element('th').classes('text-left').add(ui.label('Duration'))
                                    ui.element('th').classes('text-left').add(ui.label('Details'))

                            # Body
                            with ui.element('tbody'):
                                for log in sync_logs:
                                    details = log.details or {}
                                    success = details.get('success', False)
                                    error = details.get('error')

                                    with ui.element('tr'):
                                        # Time
                                        with ui.element('td'):
                                            DateTimeLabel.create(log.created_at, format_type='relative')

                                        # Status
                                        with ui.element('td'):
                                            if success:
                                                ui.badge('Success').classes('badge-success')
                                            else:
                                                ui.badge('Failed').classes('badge-danger')

                                        # Imported
                                        with ui.element('td').classes('text-center'):
                                            imported = details.get('imported', 0)
                                            if imported > 0:
                                                ui.label(str(imported)).classes('text-positive font-bold')
                                            else:
                                                ui.label(str(imported)).classes('text-secondary')

                                        # Updated
                                        with ui.element('td').classes('text-center'):
                                            updated = details.get('updated', 0)
                                            if updated > 0:
                                                ui.label(str(updated)).classes('text-info font-bold')
                                            else:
                                                ui.label(str(updated)).classes('text-secondary')

                                        # Deleted
                                        with ui.element('td').classes('text-center'):
                                            deleted = details.get('deleted', 0)
                                            if deleted > 0:
                                                ui.label(str(deleted)).classes('text-warning font-bold')
                                            else:
                                                ui.label(str(deleted)).classes('text-secondary')

                                        # Duration
                                        with ui.element('td'):
                                            duration_ms = details.get('duration_ms')
                                            if duration_ms is not None:
                                                if duration_ms < 1000:
                                                    ui.label(f'{duration_ms}ms').classes('text-sm')
                                                else:
                                                    ui.label(f'{duration_ms / 1000:.1f}s').classes('text-sm')
                                            else:
                                                ui.label('—').classes('text-secondary')

                                        # Details/Error
                                        with ui.element('td'):
                                            if error:
                                                with ui.row().classes('items-center gap-1'):
                                                    ui.icon('error', size='sm').classes('text-negative')
                                                    ui.label(error).classes('text-sm text-negative')
                                            else:
                                                ui.label('—').classes('text-secondary text-sm')

                # Error summary (if any recent errors)
                recent_errors = [log for log in sync_logs if log.details and not log.details.get('success', False)]
                if recent_errors:
                    ui.separator().classes('my-4')
                    with ui.element('div').classes('p-3 bg-danger-light rounded'):
                        with ui.row().classes('items-start gap-2'):
                            ui.icon('warning', color='negative')
                            with ui.column().classes('gap-1'):
                                ui.label('Recent Sync Errors').classes('font-bold text-negative')
                                ui.label(
                                    f'{len(recent_errors)} of the last {len(sync_logs)} sync attempts failed. '
                                    'Check the sync history above for details.'
                                ).classes('text-sm')

        # Placeholder Users section (if SpeedGaming enabled)
        if self.tournament.speedgaming_enabled:
            await self._render_placeholder_users_section()

    async def _render_placeholder_users_section(self):
        """Render placeholder users section for SpeedGaming integration."""
        from models import User
        from models.match_schedule import MatchPlayers, Crew
        from components.data_table import ResponsiveTable, TableColumn

        # Find placeholder users associated with this tournament's matches
        # Get all matches for this tournament
        matches = await self.tournament.matches.all()
        match_ids = [m.id for m in matches]

        # Get placeholder users from match players
        player_placeholders = await User.filter(
            is_placeholder=True,
            match_players__match_id__in=match_ids
        ).distinct().prefetch_related('match_players__match')

        # Get placeholder users from crew
        crew_placeholders = await User.filter(
            is_placeholder=True,
            crew_assignments__match_id__in=match_ids
        ).distinct().prefetch_related('crew_assignments__match')

        # Combine and deduplicate
        all_placeholder_ids = set()
        all_placeholders = []
        
        for user in player_placeholders:
            if user.id not in all_placeholder_ids:
                all_placeholder_ids.add(user.id)
                all_placeholders.append(user)
        
        for user in crew_placeholders:
            if user.id not in all_placeholder_ids:
                all_placeholder_ids.add(user.id)
                all_placeholders.append(user)

        if not all_placeholders:
            return  # No placeholder users, don't show section

        with ui.element('div').classes('card mt-4'):
            with ui.element('div').classes('card-header'):
                with ui.row().classes('items-center justify-between w-full'):
                    ui.label('Placeholder Users').classes('text-xl font-bold')
                    ui.badge(str(len(all_placeholders))).classes('badge-warning')

            with ui.element('div').classes('card-body'):
                # Info message
                with ui.element('div').classes('p-3 bg-warning-light rounded mb-4'):
                    with ui.row().classes('items-start gap-2'):
                        ui.icon('info', color='warning')
                        with ui.column().classes('gap-1'):
                            ui.label('Action Required').classes('font-bold text-warning')
                            ui.label(
                                'The following users were created as placeholders because their Discord ID '
                                'was not available in SpeedGaming. Please update the Discord ID in SpeedGaming.org '
                                'so these users can be linked to their actual accounts.'
                            ).classes('text-sm')

                # Placeholder users table
                def render_username(user: User):
                    with ui.row().classes('items-center gap-2'):
                        ui.icon('account_circle', color='warning')
                        ui.label(user.discord_username or 'Unknown').classes('font-mono')

                def render_display_name(user: User):
                    ui.label(user.display_name or user.discord_username or '—')

                def render_speedgaming_id(user: User):
                    if user.speedgaming_id:
                        ui.label(f'SG#{user.speedgaming_id}').classes('font-mono text-sm')
                    else:
                        ui.label('—').classes('text-secondary')

                async def render_matches(user: User):
                    # Get matches where this user is a player
                    player_matches = await MatchPlayers.filter(
                        user=user,
                        match_id__in=match_ids
                    ).prefetch_related('match').all()
                    
                    # Get matches where this user is crew
                    crew_matches = await Crew.filter(
                        user=user,
                        match_id__in=match_ids
                    ).prefetch_related('match').all()

                    match_count = len(set([mp.match.id for mp in player_matches] + [c.match.id for c in crew_matches]))
                    
                    if match_count > 0:
                        ui.label(f'{match_count} match{"es" if match_count != 1 else ""}').classes('text-sm')
                    else:
                        ui.label('—').classes('text-secondary')

                async def render_roles(user: User):
                    roles = []
                    
                    # Check if player
                    player_count = await MatchPlayers.filter(
                        user=user,
                        match_id__in=match_ids
                    ).count()
                    if player_count > 0:
                        roles.append('Player')
                    
                    # Check if crew
                    crew_assignments = await Crew.filter(
                        user=user,
                        match_id__in=match_ids
                    ).all()
                    
                    crew_roles = set(c.role.value for c in crew_assignments)
                    roles.extend(crew_roles)
                    
                    if roles:
                        with ui.column().classes('gap-1'):
                            for role in roles:
                                ui.badge(role).classes('badge-info text-xs')
                    else:
                        ui.label('—').classes('text-secondary')

                def render_created(user: User):
                    DateTimeLabel.create(user.created_at, format_type='relative')

                def render_actions(user: User):
                    if user.speedgaming_id:
                        ui.label(f'Update Discord ID in SpeedGaming for player/crew #{user.speedgaming_id}').classes('text-xs text-secondary')
                    else:
                        ui.label('Missing SpeedGaming ID').classes('text-xs text-warning')

                columns = [
                    TableColumn('Username', cell_render=render_username),
                    TableColumn('Display Name', cell_render=render_display_name),
                    TableColumn('SG ID', cell_render=render_speedgaming_id),
                    TableColumn('Matches', cell_render=render_matches),
                    TableColumn('Roles', cell_render=render_roles),
                    TableColumn('Created', cell_render=render_created),
                    TableColumn('Action Needed', cell_render=render_actions),
                ]

                table = ResponsiveTable(columns=columns, rows=all_placeholders)
                await table.render()
