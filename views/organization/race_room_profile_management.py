"""
Race room profile management view.

Shows a table of all profiles with actions to create, edit, delete, and set default.
"""

from nicegui import ui
from models import User
from models.organizations import Organization
from components.data_table import ResponsiveTable, TableColumn
from components.dialogs.tournaments.race_room_profile_dialog import RaceRoomProfileDialog


class RaceRoomProfileManagementView:
    """View for managing race room profiles."""

    def __init__(self, user: User, organization: Organization):
        """
        Initialize the profile management view.

        Args:
            user: Current user
            organization: Organization context
        """
        self.user = user
        self.organization = organization
        self.profiles = []
        self.table_container = None

    async def render(self):
        """Render the profile management view."""
        # RaceTime Bots Card
        await self._render_bots_card()

        ui.separator().classes('my-4')

        # Race Room Profiles Card
        with ui.element('div').classes('card'):
            with ui.element('div').classes('card-header'):
                with ui.row().classes('items-center justify-between w-full'):
                    with ui.row().classes('items-center gap-2'):
                        ui.icon('tune').classes('icon-medium')
                        ui.label('Race Room Profiles').classes('text-xl font-bold')
                    ui.button(
                        'Create Profile',
                        icon='add_circle',
                        on_click=self._create_profile
                    ).classes('btn').props('color=positive')

            with ui.element('div').classes('card-body'):
                ui.label('Manage reusable RaceTime room configuration profiles').classes('text-sm text-grey mb-4')

                # Table container
                self.table_container = ui.element('div').classes('w-full')
                await self._render_table()

    async def _render_bots_card(self):
        """Render card showing RaceTime bots assigned to this organization."""
        from application.services.racetime_bot_service import RacetimeBotService

        bot_service = RacetimeBotService()
        bots = await bot_service.get_bots_for_organization(self.organization.id, self.user)

        with ui.element('div').classes('card'):
            with ui.element('div').classes('card-header'):
                with ui.row().classes('items-center gap-2'):
                    ui.icon('smart_toy').classes('icon-medium')
                    ui.label('RaceTime Bots').classes('text-xl font-bold')

            with ui.element('div').classes('card-body'):
                if not bots:
                    with ui.element('div').classes('text-center p-4 text-grey'):
                        ui.icon('info', size='2rem')
                        ui.label('No RaceTime bots assigned').classes('text-sm mt-2')
                        ui.label('Contact an administrator to assign bots to this organization').classes('text-xs')
                else:
                    ui.label(f'{len(bots)} bot{"s" if len(bots) != 1 else ""} assigned to this organization').classes('text-sm text-grey mb-4')
                    
                    # Define table columns
                    columns = [
                        TableColumn(
                            label='Bot Name',
                            cell_render=lambda b: self._render_bot_name_cell(b)
                        ),
                        TableColumn(
                            label='Category',
                            cell_render=lambda b: self._render_bot_category_cell(b)
                        ),
                        TableColumn(
                            label='Status',
                            cell_render=lambda b: self._render_bot_status_cell(b)
                        ),
                    ]

                    # Render table
                    table = ResponsiveTable(columns=columns, rows=bots)
                    await table.render()

                    # Note about bot assignment
                    with ui.row().classes('items-center gap-2 mt-4 p-3 rounded bg-info-light'):
                        ui.icon('info', size='sm').classes('text-info')
                        ui.label('To assign additional bots to this organization, contact a global administrator.').classes('text-sm text-info')

    def _render_bot_name_cell(self, bot):
        """Render the bot name cell."""
        with ui.row().classes('items-center gap-2'):
            ui.icon('smart_toy', size='sm')
            ui.label(bot.name).classes('font-bold')

    def _render_bot_category_cell(self, bot):
        """Render the bot category cell."""
        with ui.row().classes('items-center gap-2'):
            ui.icon('category', size='sm')
            ui.label(bot.category)

    def _render_bot_status_cell(self, bot):
        """Render the bot status cell."""
        with ui.row().classes('items-center gap-2'):
            ui.icon('circle', size='sm').classes(
                'text-positive' if bot.is_healthy() else 'text-warning'
            )
            ui.label(bot.get_status_display()).classes(
                'badge badge-success' if bot.is_healthy() else 'badge badge-warning'
            )

    async def _load_profiles(self):
        """Load profiles from the service."""
        from application.services.race_room_profile_service import RaceRoomProfileService

        service = RaceRoomProfileService()
        self.profiles = await service.list_profiles(self.user, self.organization.id)

    async def _render_table(self):
        """Render the profiles table."""
        self.table_container.clear()

        # Load profiles
        await self._load_profiles()

        with self.table_container:
            if not self.profiles:
                with ui.element('div').classes('text-center p-8 text-grey'):
                    ui.icon('info', size='3rem')
                    ui.label('No profiles yet').classes('text-lg mt-2')
                    ui.label('Create your first race room profile to get started').classes('text-sm')
                return

            # Define table columns
            columns = [
                TableColumn(
                    label='Name',
                    cell_render=lambda p: self._render_name_cell(p)
                ),
                TableColumn(
                    label='Settings',
                    cell_render=lambda p: self._render_settings_cell(p)
                ),
                TableColumn(
                    label='Default',
                    cell_render=lambda p: self._render_default_cell(p)
                ),
                TableColumn(
                    label='Actions',
                    cell_render=lambda p: self._render_actions_cell(p)
                ),
            ]

            # Render table
            table = ResponsiveTable(columns=columns, rows=self.profiles)
            await table.render()

    def _render_name_cell(self, profile):
        """Render the name cell with description."""
        with ui.column().classes('gap-1'):
            ui.label(profile.name).classes('font-bold')
            if profile.description:
                ui.label(profile.description).classes('text-sm text-grey')

    def _render_settings_cell(self, profile):
        """Render a summary of settings."""
        with ui.column().classes('gap-1'):
            ui.label(f'Start: {profile.start_delay}s, Limit: {profile.time_limit}h').classes('text-sm')
            settings = []
            if profile.streaming_required:
                settings.append('Streaming Required')
            if profile.auto_start:
                settings.append('Auto-start')
            if not profile.allow_comments:
                settings.append('No Comments')
            if settings:
                ui.label(' • '.join(settings)).classes('text-sm text-grey')

    def _render_default_cell(self, profile):
        """Render the default status."""
        if profile.is_default:
            with ui.row().classes('items-center gap-1'):
                ui.icon('star', size='sm').classes('text-warning')
                ui.label('Default').classes('text-sm font-bold')
        else:
            ui.label('—').classes('text-grey')

    def _render_actions_cell(self, profile):
        """Render action buttons."""
        with ui.row().classes('gap-2'):
            if not profile.is_default:
                ui.button(
                    icon='star_outline',
                    on_click=lambda p=profile: self._set_default(p)
                ).props('flat dense round').tooltip('Set as Default')

            ui.button(
                icon='edit',
                on_click=lambda p=profile: self._edit_profile(p)
            ).props('flat dense round').tooltip('Edit')

            ui.button(
                icon='delete',
                on_click=lambda p=profile: self._delete_profile(p)
            ).props('flat dense round color=negative').tooltip('Delete')

    async def _create_profile(self):
        """Open dialog to create a new profile."""
        dialog = RaceRoomProfileDialog(
            user=self.user,
            organization_id=self.organization.id,
            profile=None,
            on_save=self._render_table
        )
        await dialog.show()

    async def _edit_profile(self, profile):
        """Open dialog to edit an existing profile."""
        dialog = RaceRoomProfileDialog(
            user=self.user,
            organization_id=self.organization.id,
            profile=profile,
            on_save=self._render_table
        )
        await dialog.show()

    async def _delete_profile(self, profile):
        """Delete a profile with confirmation."""
        from components.dialogs.common.tournament_dialogs import ConfirmDialog

        async def confirm_delete():
            from application.services.race_room_profile_service import RaceRoomProfileService

            service = RaceRoomProfileService()
            success = await service.delete_profile(
                self.user,
                self.organization.id,
                profile.id
            )

            if success:
                ui.notify(f"Profile '{profile.name}' deleted successfully!", type='positive')
                await self._render_table()
            else:
                ui.notify('Failed to delete profile', type='negative')

        dialog = ConfirmDialog(
            title='Delete Profile',
            message=f"Are you sure you want to delete the profile '{profile.name}'? This action cannot be undone.",
            on_confirm=confirm_delete
        )
        await dialog.show()

    async def _set_default(self, profile):
        """Set a profile as the default."""
        from application.services.race_room_profile_service import RaceRoomProfileService

        service = RaceRoomProfileService()
        success = await service.set_default_profile(
            self.user,
            self.organization.id,
            profile.id
        )

        if success:
            ui.notify(f"Profile '{profile.name}' set as default!", type='positive')
            await self._render_table()
        else:
            ui.notify('Failed to set default profile', type='negative')
