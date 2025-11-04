"""
RaceTime Account view for user profile.

Display and manage RaceTime.gg account linking.
"""

from __future__ import annotations
import logging
from nicegui import ui
from models import User
from components.card import Card

logger = logging.getLogger(__name__)


class RacetimeAccountView:
    """View for managing RaceTime.gg account linking."""

    def __init__(self, user: User) -> None:
        self.user = user

    async def render(self) -> None:
        """Render the RaceTime account management interface."""
        with Card.create(title='RaceTime.gg Account'):
            with ui.element('div').classes('flex flex-col gap-4'):
                # Account status
                if self.user.racetime_id:
                    # Account is linked
                    with ui.row().classes('items-center'):
                        ui.icon('link').classes('text-success')
                        with ui.column().classes('flex-1'):
                            ui.label('Account Status').classes('text-sm text-secondary')
                            ui.label('Linked').classes('badge badge-success')

                    # RaceTime username
                    with ui.row().classes('items-center'):
                        ui.icon('person').classes('text-secondary')
                        with ui.column().classes('flex-1'):
                            ui.label('RaceTime.gg Username').classes('text-sm text-secondary')
                            ui.label(self.user.racetime_name or 'Unknown').classes('font-bold')

                    # RaceTime ID
                    with ui.row().classes('items-center'):
                        ui.icon('fingerprint').classes('text-secondary')
                        with ui.column().classes('flex-1'):
                            ui.label('RaceTime.gg ID').classes('text-sm text-secondary')
                            ui.label(self.user.racetime_id).classes('font-mono')

                    ui.separator()

                    # Unlink button
                    async def handle_unlink():
                        """Handle unlinking RaceTime account."""
                        result = await ui.run_javascript(
                            'return window.WindowUtils.confirm("Are you sure you want to unlink your RaceTime.gg account?");'
                        )
                        if result:
                            await self._unlink_account()

                    ui.button('Unlink Account', on_click=handle_unlink).classes('btn').props('color=negative')

                else:
                    # Account is not linked
                    with ui.row().classes('items-center'):
                        ui.icon('link_off').classes('text-warning')
                        with ui.column().classes('flex-1'):
                            ui.label('Account Status').classes('text-sm text-secondary')
                            ui.label('Not Linked').classes('badge badge-warning')

                    ui.separator()

                    # Info about linking
                    with ui.element('div').classes('flex flex-col gap-2'):
                        ui.label('Link your RaceTime.gg account to:').classes('text-sm')
                        with ui.element('ul').classes('list-disc pl-6 text-sm'):
                            ui.label('Participate in races and tournaments').classes('list-item')
                            ui.label('Track your race history and statistics').classes('list-item')
                            ui.label('Sync your race data automatically').classes('list-item')

                    ui.separator()

                    # Link button
                    ui.button(
                        'Link RaceTime.gg Account',
                        on_click=lambda: ui.navigate.to('/racetime/link/initiate')
                    ).classes('btn btn-primary')

    async def _unlink_account(self) -> None:
        """Unlink the RaceTime account via service."""
        from application.services.user_service import UserService
        from application.repositories.user_repository import UserRepository

        try:
            # Call the service to unlink the account
            user_service = UserService()
            await user_service.unlink_racetime_account(self.user)

            # Refresh the user object
            user_repo = UserRepository()
            self.user = await user_repo.get_by_id(self.user.id)

            ui.notify('RaceTime account unlinked successfully', type='positive')
            # Reload the page to reflect changes
            ui.navigate.to('/profile')

        except Exception as e:
            logger.error("Error unlinking RaceTime account: %s", str(e), exc_info=True)
            ui.notify('An error occurred while unlinking your account', type='negative')
