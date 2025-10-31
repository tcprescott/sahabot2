"""
Dialog for confirming leaving an organization.

This module provides a confirmation dialog for users leaving organizations.
"""

from __future__ import annotations
from typing import Optional, Callable
from nicegui import ui
from components.dialogs.base_dialog import BaseDialog
import logging

logger = logging.getLogger(__name__)


class LeaveOrganizationDialog(BaseDialog):
    """Dialog for confirming leaving an organization."""

    def __init__(self, org_name: str, on_confirm: Optional[Callable[[], None]] = None):
        """Initialize the leave organization dialog.
        
        Args:
            org_name: Name of the organization to leave
            on_confirm: Callback function to call when confirmed
        """
        super().__init__()
        self.org_name = org_name
        self.on_confirm = on_confirm

    async def show(self) -> None:
        """Display the dialog."""
        self.create_dialog(
            title=f'Leave {self.org_name}?',
            icon='warning',
            max_width='dialog-card-sm',
        )
        await super().show()

    def _render_body(self) -> None:
        """Render dialog content."""
        # Warning message
        with ui.element('div').classes('alert alert-warning mb-4'):
            with ui.row().classes('items-center gap-sm'):
                ui.icon('warning').classes('icon-medium')
                ui.label('This action cannot be undone').classes('text-bold')
        
        ui.label('Are you sure you want to leave this organization?').classes('mb-2')
        ui.label('You will lose access to all organization resources and need to be re-invited to rejoin.').classes('text-secondary text-sm')

        # Actions
        with self.create_actions_row():
            ui.button('Cancel', on_click=self.close).classes('btn')
            ui.button('Leave Organization', on_click=self._handle_confirm).props('color=negative').classes('btn')

    async def _handle_confirm(self) -> None:
        """Handle confirm button click."""
        if self.on_confirm:
            await self.on_confirm()
        await self.close()
