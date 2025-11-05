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
        
        # Check permissions for each guild
        guild_permissions = await self._check_guild_permissions(discord_guilds)
        
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

                # Event duration
                ui.label('Event Duration:').classes('font-bold mb-2')
                current_duration = self.tournament.event_duration_minutes if hasattr(self.tournament, 'event_duration_minutes') else 120
                duration_input = ui.number(
                    label='Duration (minutes)',
                    value=current_duration,
                    min=15,
                    max=1440,  # 24 hours max
                    step=15,
                ).classes('w-full mb-2')
                
                # Helper text with common presets
                with ui.row().classes('gap-2 mb-2 flex-wrap'):
                    ui.button('60 min', on_click=lambda: setattr(duration_input, 'value', 60)).classes('btn btn-sm').props('outline')
                    ui.button('90 min', on_click=lambda: setattr(duration_input, 'value', 90)).classes('btn btn-sm').props('outline')
                    ui.button('120 min (default)', on_click=lambda: setattr(duration_input, 'value', 120)).classes('btn btn-sm').props('outline')
                    ui.button('180 min', on_click=lambda: setattr(duration_input, 'value', 180)).classes('btn btn-sm').props('outline')
                    ui.button('240 min', on_click=lambda: setattr(duration_input, 'value', 240)).classes('btn btn-sm').props('outline')
                
                ui.label('How long Discord events should be scheduled for (in minutes). Common: 60=1hr, 90=1.5hrs, 120=2hrs, 180=3hrs').classes('text-xs text-secondary mb-4')

                ui.separator().classes('my-4')

                # Discord servers selection
                guilds_select = None
                if discord_guilds:
                    ui.label('Discord Servers:').classes('font-bold mb-2')
                    
                    # Build guild options with permission warnings
                    guild_options = {}
                    for guild in discord_guilds:
                        has_permission = guild_permissions.get(guild.id, False)
                        if has_permission:
                            guild_options[guild.id] = guild.guild_name
                        else:
                            guild_options[guild.id] = f"{guild.guild_name} ⚠️ (Bot lacks MANAGE_EVENTS permission)"
                    
                    guilds_select = ui.select(
                        options=guild_options,
                        value=current_guild_ids,
                        label='Servers to publish events to',
                        multiple=True,
                        with_input=True,
                    ).classes('w-full mb-2')
                    
                    # Show warning if any selected guilds lack permissions
                    selected_without_perms = [
                        discord_guilds[i].guild_name 
                        for i, guild in enumerate(discord_guilds) 
                        if guild.id in current_guild_ids and not guild_permissions.get(guild.id, False)
                    ]
                    if selected_without_perms:
                        with ui.row().classes('items-center gap-2 p-3 rounded bg-warning text-white mb-2'):
                            ui.icon('warning')
                            with ui.column().classes('gap-1'):
                                ui.label('Permission Warning').classes('font-bold')
                                ui.label(f"Bot lacks MANAGE_EVENTS permission in: {', '.join(selected_without_perms)}").classes('text-sm')
                                ui.label('Events will not be created in these servers until permissions are granted').classes('text-xs')
                    
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
                        duration_input.value,
                        guilds_select.value if guilds_select else []
                    )).classes('btn').props('color=positive')

    async def _save_settings(
        self,
        create_scheduled_events: bool,
        scheduled_events_enabled: bool,
        discord_event_filter: str,
        event_duration_minutes: int,
        discord_guild_ids: list[int]
    ):
        """
        Save Discord events settings.

        Args:
            create_scheduled_events: Whether to create Discord events
            scheduled_events_enabled: Whether events are currently enabled
            discord_event_filter: Which matches should create events
            event_duration_minutes: Duration of Discord events in minutes
            discord_guild_ids: List of Discord guild IDs to publish to
        """
        try:
            # Check permissions for selected guilds
            if discord_guild_ids:
                from models import DiscordGuild
                selected_guilds = await DiscordGuild.filter(
                    id__in=discord_guild_ids,
                    organization_id=self.organization.id
                ).all()
                
                guild_permissions = await self._check_guild_permissions(selected_guilds)
                guilds_without_perms = [
                    guild.guild_name 
                    for guild in selected_guilds 
                    if not guild_permissions.get(guild.id, False)
                ]
                
                if guilds_without_perms:
                    ui.notify(
                        f"Warning: Bot lacks MANAGE_EVENTS permission in: {', '.join(guilds_without_perms)}. "
                        f"Events will not be created in these servers.",
                        type='warning',
                        timeout=10000
                    )
            
            await self.service.update_tournament(
                user=self.user,
                organization_id=self.organization.id,
                tournament_id=self.tournament.id,
                create_scheduled_events=create_scheduled_events,
                scheduled_events_enabled=scheduled_events_enabled,
                discord_event_filter=discord_event_filter,
                event_duration_minutes=event_duration_minutes,
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

    async def _check_guild_permissions(self, guilds) -> dict[int, bool]:
        """
        Check MANAGE_EVENTS permission for each guild.

        Args:
            guilds: List of DiscordGuild models to check

        Returns:
            Dictionary mapping guild_id to boolean (True if bot has permission)
        """
        from discordbot.client import get_bot_instance
        import discord
        
        bot = get_bot_instance()
        if not bot:
            # Bot not running - return False for all guilds
            return {guild.id: False for guild in guilds}
        
        permissions = {}
        for guild_model in guilds:
            try:
                # Get Discord guild object
                discord_guild = bot.get_guild(guild_model.discord_id)
                if not discord_guild:
                    permissions[guild_model.id] = False
                    continue
                
                # Get bot member
                bot_member = discord_guild.get_member(bot.user.id)
                if not bot_member:
                    permissions[guild_model.id] = False
                    continue
                
                # Check MANAGE_EVENTS permission
                has_permission = bot_member.guild_permissions.manage_events
                permissions[guild_model.id] = has_permission
                
            except Exception:
                # On any error, assume no permission
                permissions[guild_model.id] = False
        
        return permissions
