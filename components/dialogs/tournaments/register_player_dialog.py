"""
Dialog for tournament admins to register players for tournaments.
"""

from __future__ import annotations
from typing import Optional, Callable, Awaitable
from nicegui import ui
from components.dialogs.common.base_dialog import BaseDialog
from application.services.core.user_service import UserService
from application.services.organizations.organization_service import OrganizationService
from models import Organization, User, Tournament
import logging

logger = logging.getLogger(__name__)


class RegisterPlayerDialog(BaseDialog):
    """Dialog for admins to register a user for a tournament."""

    def __init__(
        self,
        admin_user: User,
        organization: Organization,
        tournament: Tournament,
        on_save: Optional[Callable[[], Awaitable[None]]] = None
    ) -> None:
        super().__init__()
        self.admin_user = admin_user
        self.organization = organization
        self.tournament = tournament
        self.on_save = on_save
        self.user_service = UserService()
        self.org_service = OrganizationService()

        # UI refs
        self.user_select: Optional[ui.select] = None

    async def show(self) -> None:
        """Display the dialog."""
        self.create_dialog(
            title=f'Register Player for {self.tournament.name}',
            icon='person_add',
            max_width='dialog-card'
        )
        await super().show()

    def _render_body(self) -> None:
        """Render dialog body with form fields."""
        with self.create_form_grid(columns=1):
            with ui.element('div'):
                ui.label('Select a user to register for this tournament').classes('font-semibold mb-2')
                
                self.user_select = ui.select(
                    label='User',
                    options={},
                    with_input=True,
                ).classes('w-full')

                ui.label('Only members of this organization will be shown').classes('text-sm text-secondary mt-1')

        with self.create_actions_row():
            ui.button('Cancel', on_click=self.close).classes('btn')
            ui.button('Register Player', on_click=self._handle_register).classes('btn').props('color=positive')

        # Load users asynchronously
        ui.timer(0.1, self._load_users, once=True)

    async def _load_users(self) -> None:
        """Load organization members."""
        try:
            # Get all members of the organization
            members = await self.org_service.list_members(self.organization.id)
            
            if not members:
                ui.notify('No members found in this organization', type='warning')
                self.user_select.options = {}
                self.user_select.update()
                return

            # Build options dict: user_id -> username
            # Note: We show discord_username (not email) per privacy guidelines
            options = {}
            for member in members:
                await member.fetch_related('user')
                if hasattr(member, 'user') and member.user:
                    options[member.user.id] = member.user.get_display_name()

            if self.user_select:
                self.user_select.options = options
                self.user_select.update()

        except Exception as e:
            logger.error("Failed to load organization members: %s", e)
            ui.notify('Failed to load users', type='negative')

    async def _handle_register(self) -> None:
        """Handle register button click."""
        if not self.user_select or not self.user_select.value:
            ui.notify('Please select a user', type='warning')
            return

        user_id = self.user_select.value

        try:
            from application.services.tournaments.tournament_service import TournamentService
            tournament_service = TournamentService()

            # Register the user via admin method
            result = await tournament_service.admin_register_user_for_tournament(
                admin_user=self.admin_user,
                organization_id=self.organization.id,
                tournament_id=self.tournament.id,
                user_id=user_id
            )

            if result:
                ui.notify('Player registered successfully', type='positive')
                if self.on_save:
                    await self.on_save()
                await self.close()
            else:
                ui.notify('Failed to register player. Check permissions or if user is already registered.', type='negative')

        except Exception as e:
            logger.error("Failed to register player: %s", e)
            ui.notify(f'Failed to register player: {str(e)}', type='negative')
