"""
Tournament Discord Events View.

Manage Discord scheduled events settings for a tournament.
"""

from __future__ import annotations
from nicegui import ui
from models import User
from models.organizations import Organization
from models.async_tournament import AsyncTournament
from application.services.tournament_service import TournamentService
from application.services.discord_scheduled_event_service import DiscordScheduledEventService


class TournamentDiscordEventsView:
    """View for managing Discord scheduled events for a tournament."""

    def __init__(self, user: User, organization: Organization, tournament: AsyncTournament):
        """
        Initialize the Discord events view.

        Args:
            user: Current user
            organization: Tournament's organization
            tournament: Tournament to manage
        """
        self.user = user
        self.organization = organization
        self.tournament = tournament
        self.service = TournamentService()
        self.discord_events_service = DiscordScheduledEventService()

    async def render(self):
        """Render the Discord events settings view."""
        # Get available Discord guilds for this organization
        from models import DiscordGuild
        discord_guilds = await DiscordGuild.filter(organization_id=self.organization.id, is_active=True).all()
        
        # Get currently selected guilds for this tournament
        await self.tournament.fetch_related('discord_event_guilds')
        current_guild_ids = [guild.id for guild in self.tournament.discord_event_guilds]

        with ui.element('div').classes('card'):
            with ui.element('div').classes('card-header'):
                with ui.row().classes('items-center justify-between w-full'):
                    ui.label('Discord Scheduled Events').classes('text-xl font-bold')
                    if self.tournament.create_scheduled_events and self.tournament.scheduled_events_enabled:
                        ui.button(
                            'Sync Events',
                            icon='sync',
                            on_click=self._sync_events
                        ).classes('btn').props('color=secondary')

            with ui.element('div').classes('card-body'):
                # Introduction
                with ui.row().classes('items-start gap-2 p-3 rounded bg-info text-white mb-4'):
                    ui.icon('info')
                    with ui.column().classes('gap-1'):
                        ui.label('Discord scheduled events will be created automatically for tournament matches').classes('font-bold')
                        ui.label('Players will receive notifications and can mark themselves as interested').classes('text-sm')

                # Enable/disable toggle
                with ui.row().classes('items-center gap-4 mb-4'):
                    ui.label('Create Discord scheduled events:').classes('font-bold')
                    create_toggle = ui.switch(value=self.tournament.create_scheduled_events)
                    ui.label('When enabled, Discord events will be created for matches').classes('text-sm text-secondary')

                # Events currently enabled toggle
                with ui.row().classes('items-center gap-4 mb-4'):
                    ui.label('Events currently enabled:').classes('font-bold')
                    enabled_toggle = ui.switch(value=self.tournament.scheduled_events_enabled)
                    ui.label('Disable this to temporarily stop creating new events').classes('text-sm text-secondary')

                ui.separator().classes('my-4')

                # Event filter
                ui.label('Which matches should create events:').classes('font-bold mb-2')
                filter_options = {
                    'all': 'All scheduled matches',
                    'stream_only': 'Only matches with assigned stream',
                    'none': 'None (same as disabled)',
                }
                # Convert enum to string value (e.g., DiscordEventFilter.ALL -> 'all')
                current_filter = self.tournament.discord_event_filter.value if self.tournament.discord_event_filter else 'all'
                filter_select = ui.select(
                    options=filter_options,
                    value=current_filter,
                    label='Event Filter',
                ).classes('w-full mb-2')
                ui.label('Filter which matches create Discord events to reduce noise and highlight important matches').classes('text-xs text-secondary mb-4')

                ui.separator().classes('my-4')

                # Discord servers selection
                guilds_select = None
                if discord_guilds:
                    ui.label('Discord Servers:').classes('font-bold mb-2')
                    guild_options = {guild.id: guild.guild_name for guild in discord_guilds}
                    guilds_select = ui.select(
                        options=guild_options,
                        value=current_guild_ids,
                        label='Servers to publish events to',
                        multiple=True,
                        with_input=True,
                    ).classes('w-full mb-2')
                    ui.label('Select which Discord servers should receive scheduled events (leave empty to use all linked servers)').classes('text-xs text-secondary mb-4')
                else:
                    with ui.row().classes('items-center gap-2 p-3 rounded bg-warning text-white mb-4'):
                        ui.icon('warning')
                        ui.label('No Discord servers linked to this organization')

                ui.separator().classes('my-4')

                # Save button
                with ui.row().classes('justify-end gap-2 mt-4'):
                    ui.button('Save Settings', on_click=lambda: self._save_settings(
                        create_toggle.value,
                        enabled_toggle.value,
                        filter_select.value,
                        guilds_select.value if guilds_select else []
                    )).classes('btn').props('color=positive')

    async def _save_settings(
        self,
        create_scheduled_events: bool,
        scheduled_events_enabled: bool,
        discord_event_filter: str,
        discord_guild_ids: list[int]
    ):
        """
        Save Discord events settings.

        Args:
            create_scheduled_events: Whether to create Discord events
            scheduled_events_enabled: Whether events are currently enabled
            discord_event_filter: Which matches should create events
            discord_guild_ids: List of Discord guild IDs to publish to
        """
        try:
            await self.service.update_tournament(
                user=self.user,
                organization_id=self.organization.id,
                tournament_id=self.tournament.id,
                create_scheduled_events=create_scheduled_events,
                scheduled_events_enabled=scheduled_events_enabled,
                discord_event_filter=discord_event_filter,
                discord_guild_ids=discord_guild_ids,
            )
            ui.notify('Discord events settings saved successfully', type='positive')
        except Exception as e:
            ui.notify(f'Failed to save settings: {str(e)}', type='negative')

    async def _sync_events(self):
        """Manually sync Discord scheduled events for this tournament."""
        try:
            ui.notify('Syncing Discord events...', type='info')
            stats = await self.discord_events_service.sync_tournament_events(
                user_id=self.user.id,
                organization_id=self.organization.id,
                tournament_id=self.tournament.id,
            )
            
            # Show results
            created = stats.get('created', 0)
            updated = stats.get('updated', 0)
            deleted = stats.get('deleted', 0)
            skipped = stats.get('skipped', 0)
            
            message = f"Sync complete: {created} created, {updated} updated, {deleted} deleted, {skipped} skipped"
            ui.notify(message, type='positive')
            
        except Exception as e:
            ui.notify(f'Failed to sync events: {str(e)}', type='negative')
