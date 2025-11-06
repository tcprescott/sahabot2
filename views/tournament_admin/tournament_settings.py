"""
Tournament Settings View.

Manage general tournament settings.
"""

from __future__ import annotations
from nicegui import ui
from models import User
from models.organizations import Organization
from models.async_tournament import AsyncTournament


class TournamentSettingsView:
    """View for managing general tournament settings."""

    def __init__(self, user: User, organization: Organization, tournament: AsyncTournament):
        """
        Initialize the settings view.

        Args:
            user: Current user
            organization: Tournament's organization
            tournament: Tournament to manage
        """
        self.user = user
        self.organization = organization
        self.tournament = tournament

    async def render(self):
        """Render the tournament settings view."""
        with ui.element('div').classes('card'):
            with ui.element('div').classes('card-header'):
                ui.label('Tournament Settings').classes('text-xl font-bold')

            with ui.element('div').classes('card-body'):
                ui.label('Configure general tournament settings').classes('text-sm text-grey mb-4')

                # Basic settings
                ui.label('Name:').classes('font-bold mb-2')
                name_input = ui.input(value=self.tournament.name).classes('w-full mb-4')

                ui.label('Description:').classes('font-bold mb-2')
                description_input = ui.textarea(
                    value=self.tournament.description or ''
                ).classes('w-full mb-4')

                # Status
                with ui.row().classes('items-center gap-4 mb-4'):
                    ui.label('Active:')
                    active_toggle = ui.checkbox(value=self.tournament.is_active)

                with ui.row().classes('items-center gap-4 mb-4'):
                    ui.label('Enable Tracker:')
                    tracker_toggle = ui.checkbox(value=self.tournament.tracker_enabled or False)

                ui.separator().classes('my-4')

                # SpeedGaming Integration Section
                ui.label('SpeedGaming Integration').classes('text-lg font-bold mb-2')
                ui.label('Import tournament matches from SpeedGaming.org automatically').classes('text-sm text-grey mb-4')

                speedgaming_enabled = ui.checkbox(
                    'Enable SpeedGaming Integration',
                    value=self.tournament.speedgaming_enabled
                ).classes('mb-2')

                # Warning message when enabled
                with ui.row().classes('items-start gap-2 mb-4 p-3 bg-warning-light rounded') as warning_row:
                    ui.icon('warning', color='warning')
                    with ui.column().classes('gap-1'):
                        ui.label('Important:').classes('font-bold text-warning')
                        ui.label('• Match schedule will be READ-ONLY').classes('text-sm')
                        ui.label('• Updates sync every 5 minutes from SpeedGaming').classes('text-sm')
                        ui.label('• You cannot manually create or edit matches').classes('text-sm')

                # Show warning only when enabled
                warning_row.bind_visibility_from(speedgaming_enabled, 'value')

                # Event slug input
                with ui.column().classes('w-full mb-4') as slug_container:
                    speedgaming_event_slug = ui.input(
                        'SpeedGaming Event Slug',
                        placeholder='e.g., alttprleague',
                        value=self.tournament.speedgaming_event_slug or ''
                    ).classes('w-full')
                    ui.label(
                        'The event slug from SpeedGaming.org (found in the event URL)'
                    ).classes('text-caption text-grey')

                # Show slug input only when enabled
                slug_container.bind_visibility_from(speedgaming_enabled, 'value')

                ui.separator().classes('my-4')

                # Save button
                with ui.row().classes('justify-end mt-4'):
                    ui.button('Save Settings', on_click=lambda: self._save_settings(
                        name_input.value,
                        description_input.value,
                        active_toggle.value,
                        tracker_toggle.value,
                        speedgaming_enabled.value,
                        speedgaming_event_slug.value
                    )).classes('btn').props('color=positive')

    async def _save_settings(
        self,
        name: str,
        description: str,
        is_active: bool,
        tracker_enabled: bool,
        speedgaming_enabled: bool,
        speedgaming_event_slug: str
    ):
        """
        Save tournament settings.

        Args:
            name: Tournament name
            description: Tournament description
            is_active: Whether tournament is active
            tracker_enabled: Whether tracker is enabled
            speedgaming_enabled: Whether SpeedGaming integration is enabled
            speedgaming_event_slug: SpeedGaming event slug
        """
        from application.services.tournaments.tournament_service import TournamentService
        from components.dialogs import ConfirmDialog

        # Validate SpeedGaming settings
        if speedgaming_enabled and not speedgaming_event_slug:
            ui.notify('Event slug is required when SpeedGaming is enabled', type='negative')
            return

        # Confirm if enabling SpeedGaming for the first time
        if speedgaming_enabled and not self.tournament.speedgaming_enabled:
            dialog = ConfirmDialog(
                title='Enable SpeedGaming Integration?',
                message=(
                    'This will make the tournament schedule READ-ONLY. '
                    'All matches must be managed through SpeedGaming. Continue?'
                )
            )
            await dialog.show()
            if not dialog.result:
                return

        service = TournamentService()
        try:
            await service.update_tournament(
                user=self.user,
                organization_id=self.organization.id,
                tournament_id=self.tournament.id,
                name=name,
                description=description,
                is_active=is_active,
                tracker_enabled=tracker_enabled,
                speedgaming_enabled=speedgaming_enabled,
                speedgaming_event_slug=speedgaming_event_slug if speedgaming_enabled else None
            )

            ui.notify('Tournament settings saved successfully', type='positive')
            # Refresh the page to show updated tournament name in header
            ui.navigate.reload()
        except ValueError as e:
            ui.notify(str(e), type='negative')
        except Exception as e:
            ui.notify(f'Error saving settings: {str(e)}', type='negative')
