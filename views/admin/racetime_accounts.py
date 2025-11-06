"""RaceTime Accounts admin view."""

import logging
from nicegui import ui
from models import User
from application.services.core.user_service import UserService
from components import Card
from components.datetime_label import DateTimeLabel
from components.dialogs.admin.racetime_unlink_dialog import RacetimeUnlinkDialog

logger = logging.getLogger(__name__)


class RacetimeAccountsView:
    """Admin view for managing RaceTime linked accounts."""

    def __init__(self, admin_user: User):
        """
        Initialize the RaceTime accounts admin view.

        Args:
            admin_user: Admin user viewing the accounts
        """
        self.admin_user = admin_user
        self.user_service = UserService()
        self.search_query = ""
        self.accounts: list[User] = []
        self.stats: dict = {}
        self.container = None

    async def render(self):
        """Render the admin view."""
        # Load initial data
        await self._load_data()

        with ui.element('div').classes('w-full'):
            # Stats card
            await self._render_stats()

            # Search and filter
            await self._render_search()

            # Accounts list
            self.container = ui.element('div').classes('w-full')
            with self.container:
                await self._render_accounts()

    async def _render_stats(self):
        """Render statistics card."""
        with Card.create(title='RaceTime Link Statistics'):
            with ui.row().classes('w-full gap-4'):
                # Total users
                with ui.element('div').classes('flex-1'):
                    ui.label(str(self.stats.get('total_users', 0))).classes('text-2xl font-bold')
                    ui.label('Total Users').classes('text-sm text-gray-600')

                # Linked users
                with ui.element('div').classes('flex-1'):
                    ui.label(str(self.stats.get('linked_users', 0))).classes('text-2xl font-bold text-green-600')
                    ui.label('Linked Accounts').classes('text-sm text-gray-600')

                # Unlinked users
                with ui.element('div').classes('flex-1'):
                    ui.label(str(self.stats.get('unlinked_users', 0))).classes('text-2xl font-bold text-gray-600')
                    ui.label('Not Linked').classes('text-sm text-gray-600')

                # Link percentage
                with ui.element('div').classes('flex-1'):
                    percentage = self.stats.get('link_percentage', 0)
                    ui.label(f'{percentage}%').classes('text-2xl font-bold text-blue-600')
                    ui.label('Link Rate').classes('text-sm text-gray-600')

    async def _render_search(self):
        """Render search and filter controls."""
        with Card.create(title='Search'):
            with ui.row().classes('w-full gap-2 items-center'):
                search_input = ui.input(
                    label='Search by RaceTime username',
                    placeholder='Enter RaceTime username...'
                ).classes('flex-1')

                ui.button(
                    'Search',
                    icon='search',
                    on_click=lambda: self._perform_search(search_input.value)
                ).classes('btn btn-primary')

                ui.button(
                    'Clear',
                    icon='clear',
                    on_click=lambda: self._clear_search(search_input)
                ).classes('btn btn-secondary')

    async def _render_accounts(self):
        """Render accounts list."""
        if not self.accounts:
            with Card.create():
                ui.label('No linked accounts found').classes('text-center text-gray-600')
            return

        with ui.element('div').classes('w-full gap-2'):
            for account in self.accounts:
                await self._render_account_card(account)

    async def _render_account_card(self, account: User):
        """Render individual account card."""
        with Card.create():
            with ui.row().classes('w-full items-center gap-4'):
                # User icon
                ui.icon('person', size='lg').classes('text-blue-600')

                # Account info
                with ui.column().classes('flex-1 gap-1'):
                    # Discord username
                    with ui.row().classes('gap-2 items-center'):
                        ui.label(account.discord_username).classes('font-bold')
                        ui.label(f'(Discord ID: {account.discord_id})').classes('text-sm text-gray-600')

                    # RaceTime info
                    with ui.row().classes('gap-2 items-center'):
                        ui.icon('sports_score', size='sm').classes('text-green-600')
                        ui.link(
                            account.racetime_name,
                            f'https://racetime.gg/user/{account.racetime_id}',
                            new_tab=True
                        ).classes('text-blue-600')
                        ui.label(f'({account.racetime_id})').classes('text-sm text-gray-600')

                    # Linked since
                    if account.updated_at:
                        with ui.row().classes('gap-2 items-center'):
                            ui.label('Linked:').classes('text-sm text-gray-600')
                            DateTimeLabel.create(account.updated_at, format_type='relative')

                # Actions
                with ui.column().classes('gap-2'):
                    ui.button(
                        'Unlink',
                        icon='link_off',
                        on_click=lambda a=account: self._unlink_account(a)
                    ).classes('btn btn-danger')

    async def _load_data(self):
        """Load accounts and statistics."""
        # Load stats
        self.stats = await self.user_service.get_racetime_link_statistics(
            admin_user=self.admin_user
        )

        # Load accounts
        if self.search_query:
            self.accounts = await self.user_service.search_racetime_accounts(
                admin_user=self.admin_user,
                query=self.search_query
            )
        else:
            self.accounts = await self.user_service.get_all_racetime_accounts(
                admin_user=self.admin_user,
                limit=100,  # Show first 100 accounts
                offset=0
            )

        logger.info(
            "Admin %s viewed RaceTime accounts (query: %s, count: %s)",
            self.admin_user.id,
            self.search_query or 'none',
            len(self.accounts)
        )

    async def _perform_search(self, query: str):
        """Perform search."""
        self.search_query = query.strip()
        await self._refresh()

    async def _clear_search(self, search_input):
        """Clear search."""
        search_input.value = ''
        self.search_query = ''
        await self._refresh()

    async def _refresh(self):
        """Refresh the view."""
        await self._load_data()

        # Re-render accounts
        self.container.clear()
        with self.container:
            await self._render_accounts()

    async def _unlink_account(self, account: User):
        """Open unlink confirmation dialog."""
        dialog = RacetimeUnlinkDialog(
            user=account,
            admin_user=self.admin_user,
            on_unlink=self._refresh
        )
        await dialog.show()
