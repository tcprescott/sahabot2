"""
Admin logs view - real-time application log viewer.

Provides a comprehensive interface for viewing application logs in real-time,
with filtering by log level and search capabilities.
"""

from nicegui import ui
from models import User
from application.utils.log_handler import get_log_handler, LogRecord
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class AdminLogsView:
    """Admin log viewer with real-time updates and filtering."""

    # Log level colors for UI
    LEVEL_COLORS = {
        'DEBUG': 'text-gray-500',
        'INFO': 'text-blue-500',
        'WARNING': 'text-yellow-600',
        'ERROR': 'text-red-600',
        'CRITICAL': 'text-red-900 font-bold',
    }

    def __init__(self, current_user: User):
        """
        Initialize the admin logs view.

        Args:
            current_user: Currently authenticated admin user
        """
        self.current_user = current_user
        self.log_handler = get_log_handler()

        # State
        self.level_filter: Optional[str] = None
        self.search_filter: Optional[str] = None
        self.auto_scroll = True
        self.log_container = None
        self.timer = None

    async def render(self):
        """Render the log viewer interface."""
        with ui.column().classes('full-width gap-md'):
            # Header section
            with ui.element('div').classes('card'):
                with ui.element('div').classes('card-header'):
                    ui.label('Application Logs').classes('text-xl font-bold')
                with ui.element('div').classes('card-body'):
                    ui.label(
                        'Real-time view of application logs. This shows recent logs from the application, '
                        'complementing the error tracking provided by Sentry.io.'
                    ).classes('text-secondary')

            # Controls section
            with ui.element('div').classes('card'):
                with ui.element('div').classes('card-body'):
                    with ui.row().classes('full-width gap-4 items-center flex-wrap'):
                        # Level filter
                        level_select = ui.select(
                            label='Log Level',
                            options=['ALL', 'DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
                            value='ALL'
                        ).classes('w-40')
                        level_select.on('update:model-value', self._on_level_filter)

                        # Search filter
                        search_input = ui.input(
                            label='Search',
                            placeholder='Filter by message or logger name'
                        ).classes('flex-grow')
                        search_input.on('update:model-value', self._on_search_filter)

                        # Auto-scroll toggle
                        auto_scroll_switch = ui.switch('Auto-scroll', value=True)
                        auto_scroll_switch.on('update:model-value', self._on_auto_scroll_toggle)

                        # Action buttons
                        with ui.row().classes('gap-2'):
                            ui.button(
                                'Refresh',
                                icon='refresh',
                                on_click=self._refresh_logs
                            ).classes('btn').props('flat')

                            ui.button(
                                'Clear Logs',
                                icon='clear_all',
                                on_click=self._clear_logs
                            ).classes('btn').props('flat color=warning')

                            ui.button(
                                'Download',
                                icon='download',
                                on_click=self._download_logs
                            ).classes('btn').props('flat')

            # Log display section
            with ui.element('div').classes('card'):
                with ui.element('div').classes('card-body'):
                    # Stats
                    count = self.log_handler.get_count()
                    ui.label(f'Showing {count} log records (max {self.log_handler.max_records})').classes('text-sm text-secondary mb-2')

                    # Log container with scrolling
                    with ui.element('div').classes('border rounded p-2 bg-gray-50').style('height: 600px; overflow-y: auto; font-family: monospace; font-size: 0.875rem') as scroll_area:
                        self.log_container = ui.column().classes('full-width gap-1')
                        self.scroll_area = scroll_area

                    # Initial render
                    await self._refresh_logs()

                    # Set up periodic refresh (every 2 seconds)
                    self.timer = ui.timer(2.0, self._refresh_logs)

    async def _refresh_logs(self):
        """Refresh the log display."""
        if not self.log_container:
            return

        # Get filtered logs
        level = None if self.level_filter == 'ALL' else self.level_filter
        records = self.log_handler.get_records(
            level=level,
            search=self.search_filter
        )

        # Clear and render logs
        self.log_container.clear()
        with self.log_container:
            if not records:
                ui.label('No logs to display').classes('text-secondary italic')
            else:
                for record in records:
                    self._render_log_record(record)

        # Auto-scroll to bottom if enabled
        if self.auto_scroll and self.scroll_area:
            # Use JavaScript to scroll to bottom
            ui.run_javascript(f'''
                const element = getElement({self.scroll_area.id});
                if (element) {{
                    element.scrollTop = element.scrollHeight;
                }}
            ''')

    def _render_log_record(self, record: LogRecord):
        """
        Render a single log record.

        Args:
            record: The log record to render
        """
        # Get color for level
        color_class = self.LEVEL_COLORS.get(record.level, 'text-gray-700')

        # Format timestamp
        timestamp = record.timestamp.strftime('%Y-%m-%d %H:%M:%S')

        with ui.row().classes('full-width gap-2 items-start'):
            # Timestamp
            ui.label(timestamp).classes('text-gray-500 text-xs').style('min-width: 140px')

            # Level badge
            ui.label(record.level).classes(f'{color_class} text-xs font-bold').style('min-width: 60px')

            # Logger name
            ui.label(record.logger_name).classes('text-gray-600 text-xs').style('min-width: 200px; max-width: 200px; overflow: hidden; text-overflow: ellipsis')

            # Message
            ui.label(record.message).classes('text-gray-800 text-xs flex-grow').style('word-break: break-word')

        # Show exception info if present
        if record.exc_info:
            with ui.element('div').classes('ml-8 mt-1 p-2 bg-red-50 border-l-4 border-red-500 rounded'):
                ui.label(record.exc_info).classes('text-red-800 text-xs whitespace-pre-wrap').style('font-family: monospace')

    async def _on_level_filter(self, e):
        """Handle level filter change."""
        value = e.args[0] if e.args else 'ALL'
        self.level_filter = value if value != 'ALL' else None
        await self._refresh_logs()

    async def _on_search_filter(self, e):
        """Handle search filter change."""
        value = e.args[0] if e.args else ''
        self.search_filter = value.strip() if value and value.strip() else None
        await self._refresh_logs()

    def _on_auto_scroll_toggle(self, e):
        """Handle auto-scroll toggle."""
        self.auto_scroll = e.args[0] if e.args else False

    async def _clear_logs(self):
        """Clear all stored logs."""
        # Confirm action
        confirm = ui.dialog()
        with confirm:
            with ui.element('div').classes('card'):
                with ui.element('div').classes('card-header'):
                    ui.label('Clear Logs').classes('text-lg font-bold')
                with ui.element('div').classes('card-body'):
                    ui.label('Are you sure you want to clear all stored logs?').classes('mb-4')
                    with ui.row().classes('dialog-actions'):
                        ui.button('Cancel', on_click=confirm.close).classes('btn')

                        async def do_clear():
                            self.log_handler.clear()
                            confirm.close()
                            await self._refresh_logs()
                            ui.notify('Logs cleared', type='positive')

                        ui.button('Clear', on_click=do_clear).props('color=warning').classes('btn')
        confirm.open()

    async def _download_logs(self):
        """Download logs as a text file."""
        # Get all logs
        records = self.log_handler.get_records(
            level=None if self.level_filter == 'ALL' else self.level_filter,
            search=self.search_filter
        )

        if not records:
            ui.notify('No logs to download', type='warning')
            return

        # Format logs as text
        lines = []
        for record in records:
            timestamp = record.timestamp.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
            line = f"{timestamp} - {record.logger_name} - {record.level} - {record.message}"
            lines.append(line)
            if record.exc_info:
                lines.append(record.exc_info)
                lines.append('')

        content = '\n'.join(lines)

        # Generate timestamp for filename
        from datetime import datetime, timezone
        timestamp = datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')

        # Trigger download using JavaScript
        # Create a data URL and trigger download
        ui.run_javascript(f'''
            const content = {repr(content)};
            const blob = new Blob([content], {{ type: 'text/plain' }});
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = 'sahabot2_logs_{timestamp}.txt';
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);
        ''')

        ui.notify('Logs downloaded', type='positive')
