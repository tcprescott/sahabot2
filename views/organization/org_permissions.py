"""
Organization Permissions view.

Display available permission types for this organization.
"""

from __future__ import annotations
from typing import Any
from nicegui import ui
from models import Organization
from components.card import Card
from application.services.organizations.organization_service import OrganizationService


class OrganizationPermissionsView:
    """Display organization permission types (read-only)."""

    def __init__(self, organization: Organization, user: Any) -> None:
        self.organization = organization
        self.user = user
        self.service = OrganizationService()
        self.container = None

    async def _refresh(self) -> None:
        """Refresh the permissions list."""
        if self.container:
            self.container.clear()
            with self.container:
                await self._render_content()

    async def _render_content(self) -> None:
        """Render the available permission types."""
        available_types = self.service.list_available_permission_types()

        with Card.create(title='Available Permission Types'):
            ui.label('These permission types can be assigned to organization members.').classes('mb-4 text-secondary')

            # Display permissions as a list
            for ptype in available_types:
                with ui.element('div').classes('mb-3 p-3 border rounded'):
                    with ui.row().classes('items-center gap-2 mb-1'):
                        ui.icon('verified_user').classes('text-primary')
                        ui.label(ptype['name']).classes('text-lg font-bold')
                    ui.label(ptype['description']).classes('text-secondary')

            ui.separator().classes('my-4')
            ui.label('To assign permissions to members, go to the Members tab.').classes('text-sm text-secondary italic')

    async def render(self) -> None:
        """Render the permissions view."""
        self.container = ui.column().classes('full-width')
        with self.container:
            await self._render_content()
