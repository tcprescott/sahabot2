"""RaceTime account administrative unlink dialog."""

from nicegui import ui
from models import User
from components.dialogs.common.base_dialog import BaseDialog
from application.services.user_service import UserService


class RacetimeUnlinkDialog(BaseDialog):
    """Dialog for administratively unlinking RaceTime accounts."""

    def __init__(self, user: User, admin_user: User, on_unlink=None):
        """
        Initialize the unlink dialog.

        Args:
            user: User whose account will be unlinked
            admin_user: Admin user performing the action
            on_unlink: Optional callback after successful unlink
        """
        super().__init__()
        self.user = user
        self.admin_user = admin_user
        self.on_unlink = on_unlink
        self.user_service = UserService()

    async def show(self):
        """Display the dialog."""
        self.create_dialog(
            title='Unlink RaceTime Account',
            icon='link_off',
            max_width='500px'
        )

        await super().show()

    def _render_body(self):
        """Render dialog content."""
        # Warning message
        with ui.element('div').classes('w-full'):
            ui.label('⚠️ Administrative Account Unlinking').classes('text-lg font-bold text-orange-600')
            ui.separator()

            # User info
            self.create_section_title('User Information')
            self.create_info_row('Discord Username', self.user.discord_username)
            self.create_info_row('Discord ID', str(self.user.discord_id))

            ui.separator()

            # RaceTime info
            self.create_section_title('RaceTime Account')
            self.create_info_row('RaceTime Username', self.user.racetime_name)
            self.create_info_row('RaceTime ID', self.user.racetime_id)

            ui.separator()

            # Confirmation message
            with ui.element('div').classes('w-full bg-red-50 p-3 rounded'):
                ui.label('This will unlink the RaceTime account from this user.').classes('text-sm')
                ui.label('The user will need to re-link their account if they want to use RaceTime features.').classes('text-sm text-gray-600 mt-2')

        ui.separator()

        # Actions
        with self.create_actions_row():
            ui.button('Cancel', on_click=self.close).classes('btn')
            ui.button(
                'Unlink Account',
                on_click=self._unlink,
                icon='link_off'
            ).classes('btn').props('color=negative')

    async def _unlink(self):
        """Unlink the account."""
        # Call service
        result = await self.user_service.admin_unlink_racetime_account(
            user_id=self.user.id,
            admin_user=self.admin_user
        )

        if not result:
            ui.notify('Failed to unlink account', type='negative')
            return

        ui.notify(
            f'RaceTime account unlinked from {self.user.discord_username}',
            type='positive'
        )

        # Call callback
        if self.on_unlink:
            await self.on_unlink()

        await self.close()
