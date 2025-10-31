"""
Organization Members view.

Manage organization members and their roles.
"""

from __future__ import annotations
from typing import Any
from nicegui import ui
from models import Organization
from components.card import Card


class OrganizationMembersView:
    """Manage organization members."""

    def __init__(self, organization: Organization, user: Any) -> None:
        self.organization = organization
        self.user = user
        self.container = None

    async def _refresh(self) -> None:
        """Refresh the members list."""
        if self.container:
            self.container.clear()
            with self.container:
                await self._render_content()

    async def _render_content(self) -> None:
        """Render the members list and controls."""
        with Card.create(title='Organization Members'):
            with ui.row().classes('w-full justify-between mb-2'):
                ui.label('Manage who has access to this organization.')
                ui.button('Add Member', icon='person_add').props('color=positive').classes('btn')
            
            # Placeholder - will be populated with actual members
            with ui.element('div').classes('text-center mt-4'):
                ui.icon('people').classes('text-secondary icon-large')
                ui.label('No members yet').classes('text-secondary')
                ui.label('Add members to get started').classes('text-secondary text-sm')

    async def render(self) -> None:
        """Render the members view."""
        self.container = ui.column().classes('full-width')
        with self.container:
            await self._render_content()
