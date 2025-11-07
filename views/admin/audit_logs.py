"""
Admin audit logs view.

Provides a comprehensive interface for viewing all audit logs across the system.
"""

from nicegui import ui
from components.data_table import ResponsiveTable, TableColumn
from components.empty_state import EmptyState
from models import User
from application.services.core.audit_service import AuditService
from components.datetime_label import DateTimeLabel
from views.utils.audit_log_utils import render_audit_log_details
import logging

logger = logging.getLogger(__name__)


class AdminAuditLogsView:
    """Admin audit logs view with filtering and pagination."""

    def __init__(self, current_user: User):
        """
        Initialize the admin audit logs view.

        Args:
            current_user: Currently authenticated admin user
        """
        self.current_user = current_user
        self.audit_service = AuditService()

        # State
        self.audit_logs = []
        self.total_count = 0
        self.current_page = 0
        self.page_size = 50
        self.action_filter = None
        self.user_filter = None
        self.org_filter = None
        self.table_container = None

    async def render(self):
        """Render the audit logs interface."""
        with ui.column().classes('full-width gap-md'):
            # Header section
            with ui.element('div').classes('card'):
                with ui.element('div').classes('card-header'):
                    ui.label('Audit Logs').classes('text-xl font-bold')
                with ui.element('div').classes('card-body'):
                    ui.label(
                        'View all system audit events including user actions, '
                        'permission changes, and system operations.'
                    ).classes('text-secondary')

            # Filters and controls
            with ui.element('div').classes('card'):
                with ui.element('div').classes('card-body'):
                    with ui.row().classes('full-width gap-4 items-center'):
                        # Action filter
                        action_input = ui.input(
                            label='Filter by action',
                            placeholder='e.g., user_login, tournament_created'
                        ).classes('flex-grow')
                        action_input.on(
                            'update:model-value',
                            lambda e: self._on_action_filter(e.args)
                        )

                        # Refresh button
                        ui.button(
                            icon='refresh',
                            on_click=self._refresh_logs
                        ).classes('btn').props('flat')

            # Audit logs table
            self.table_container = ui.column().classes('full-width')
            await self._refresh_logs()

    async def _refresh_logs(self):
        """Refresh the audit logs table."""
        if not self.table_container:
            return

        # Fetch audit logs
        offset = self.current_page * self.page_size
        self.audit_logs, self.total_count = await self.audit_service.list_audit_logs(
            limit=self.page_size,
            offset=offset,
            action=self.action_filter,
            user_id=self.user_filter,
            organization_id=self.org_filter,
        )

        # Clear and render table
        self.table_container.clear()
        with self.table_container:
            await self._render_table()
            self._render_pagination()

    async def _render_table(self):
        """Render the audit logs table."""
        if not self.audit_logs:
            EmptyState.no_items(
                item_name='audit logs',
                message='No audit logs match your filters',
                icon='history',
                in_card=True
            )
            return

        columns = [
            TableColumn(
                label='Timestamp',
                cell_render=lambda log: DateTimeLabel.create(
                    log.created_at,
                    format_type='datetime'
                )
            ),
            TableColumn(
                label='User',
                cell_render=lambda log: ui.label(
                    log.user.get_display_name() if log.user else 'System'
                )
            ),
            TableColumn(
                label='Action',
                cell_render=lambda log: ui.label(log.action).classes('font-mono text-sm')
            ),
            TableColumn(
                label='Organization',
                cell_render=lambda log: ui.label(
                    f'Org #{log.organization_id}' if log.organization_id else 'Global'
                ).classes('text-sm')
            ),
            TableColumn(
                label='Details',
                cell_render=render_audit_log_details
            ),
        ]

        table = ResponsiveTable(columns=columns, rows=self.audit_logs)
        await table.render()

    def _render_pagination(self):
        """Render pagination controls."""
        if self.total_count <= self.page_size:
            return

        total_pages = (self.total_count + self.page_size - 1) // self.page_size
        current_page = self.current_page + 1

        with ui.element('div').classes('card'):
            with ui.element('div').classes('card-body'):
                with ui.row().classes('items-center justify-between full-width'):
                    # Page info
                    start = self.current_page * self.page_size + 1
                    end = min((self.current_page + 1) * self.page_size, self.total_count)
                    ui.label(
                        f'Showing {start}-{end} of {self.total_count} logs'
                    ).classes('text-secondary')

                    # Navigation buttons
                    with ui.row().classes('gap-2'):
                        ui.button(
                            icon='chevron_left',
                            on_click=self._previous_page
                        ).classes('btn').props('flat').set_enabled(self.current_page > 0)

                        ui.label(f'Page {current_page} of {total_pages}')

                        ui.button(
                            icon='chevron_right',
                            on_click=self._next_page
                        ).classes('btn').props('flat').set_enabled(
                            self.current_page < total_pages - 1
                        )

    async def _on_action_filter(self, value: str):
        """Handle action filter change."""
        self.action_filter = value.strip() if value and value.strip() else None
        self.current_page = 0
        await self._refresh_logs()

    async def _previous_page(self):
        """Navigate to previous page."""
        if self.current_page > 0:
            self.current_page -= 1
            await self._refresh_logs()

    async def _next_page(self):
        """Navigate to next page."""
        total_pages = (self.total_count + self.page_size - 1) // self.page_size
        if self.current_page < total_pages - 1:
            self.current_page += 1
            await self._refresh_logs()
