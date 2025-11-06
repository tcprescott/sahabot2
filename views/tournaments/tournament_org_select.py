"""
Tournament Organization Selector View.

Allows users to choose which organization's tournaments to view.
"""

from __future__ import annotations
from nicegui import ui
from models import User
from components.card import Card
from application.services.organizations.organization_service import OrganizationService


class TournamentOrgSelectView:
    """View for selecting an organization to view tournaments."""

    def __init__(self, user: User) -> None:
        self.user = user
        self.service = OrganizationService()

    async def render(self) -> None:
        """Render the organization selection view."""
        # Get all organizations the user is a member of via service
        members = await self.service.list_user_memberships(self.user.id)
        
        with Card.create(title='Select Organization'):
            if not members:
                with ui.element('div').classes('text-center mt-4'):
                    ui.icon('group').classes('text-secondary icon-large')
                    ui.label('You are not a member of any organizations').classes('text-secondary')
                    ui.label('Ask an administrator to invite you to an organization').classes('text-secondary text-sm')
            else:
                ui.label('Choose an organization to view:').classes('mb-4')
                
                with ui.element('div').classes('flex flex-col gap-4'):
                    for member in members:
                        org = member.organization
                        
                        with ui.element('div').classes('card'):
                            with ui.element('div').classes('card-body'):
                                with ui.row().classes('w-full items-center justify-between'):
                                    with ui.column().classes('gap-1'):
                                        ui.label(org.name).classes('text-lg font-bold')
                                        if org.description:
                                            ui.label(org.description).classes('text-sm text-secondary')
                                    
                                    ui.button(
                                        'View Organization',
                                        icon='arrow_forward',
                                        on_click=lambda o=org: ui.navigate.to(f'/org/{o.id}')
                                    ).classes('btn btn-primary')
