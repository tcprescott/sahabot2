"""
Organization Overview view.

Displays summary information and stats for an organization.
"""

from __future__ import annotations
from typing import Any
from nicegui import ui
from models import Organization, OrganizationMember
from models.async_tournament import AsyncTournament
from models.match_schedule import Tournament
from components.card import Card
from components.datetime_label import DateTimeLabel


class OrganizationOverviewView:
    """Overview dashboard for an organization."""

    def __init__(self, organization: Organization, user: Any) -> None:
        self.organization = organization
        self.user = user

    async def render(self) -> None:
        """Render the organization overview."""
        # Check if user can admin this org
        from application.services.organization_service import OrganizationService
        org_service = OrganizationService()
        can_admin = await org_service.user_can_admin_org(self.user, self.organization.id)
        can_manage_tournaments = await org_service.user_can_manage_tournaments(self.user, self.organization.id)
        can_access_admin = can_admin or can_manage_tournaments
        
        # Get member count
        member_count = await OrganizationMember.filter(organization_id=self.organization.id).count()
        
        # Get active tournaments
        active_tournaments = await Tournament.filter(
            organization_id=self.organization.id,
            is_active=True
        ).all()
        
        # Get active async tournaments
        active_async_tournaments = await AsyncTournament.filter(
            organization_id=self.organization.id,
            is_active=True
        ).all()
        
        # Welcome card
        with Card.create(title='Organization Overview'):
            with ui.column().classes('gap-md'):
                with ui.row().classes('w-full items-center justify-between'):
                    ui.label(f'Welcome to {self.organization.name}').classes('text-xl')
                    # Admin button if user has permissions
                    if can_access_admin:
                        ui.button(
                            'Administration',
                            icon='admin_panel_settings',
                            on_click=lambda: ui.navigate.to(f'/orgs/{self.organization.id}/admin')
                        ).classes('btn btn-primary')
                
                if self.organization.description:
                    ui.label(self.organization.description).classes('text-secondary')
                
                ui.separator()
                
                # Info rows
                with ui.row().classes('gap-md'):
                    ui.label('Status:').classes('font-semibold')
                    if self.organization.is_active:
                        with ui.row().classes('items-center gap-sm'):
                            ui.icon('check_circle').classes('text-positive')
                            ui.label('Active')
                    else:
                        with ui.row().classes('items-center gap-sm'):
                            ui.icon('cancel').classes('text-negative')
                            ui.label('Inactive')
                
                with ui.row().classes('gap-md'):
                    ui.label('Created:').classes('font-semibold')
                    DateTimeLabel.datetime(self.organization.created_at)
                
                with ui.row().classes('gap-md'):
                    ui.label('Last Updated:').classes('font-semibold')
                    DateTimeLabel.datetime(self.organization.updated_at)
        
        # Stats cards
        with ui.row().classes('w-full gap-md mt-2'):
            with Card.create(title='Members', classes='flex-1'):
                ui.label(str(member_count)).classes('text-4xl font-bold')
                ui.label('Total members').classes('text-secondary')
            
            with Card.create(title='Active Tournaments', classes='flex-1'):
                ui.label(str(len(active_tournaments))).classes('text-4xl font-bold')
                ui.label('Currently running').classes('text-secondary')
            
            with Card.create(title='Active Async Tournaments', classes='flex-1'):
                ui.label(str(len(active_async_tournaments))).classes('text-4xl font-bold')
                ui.label('Currently running').classes('text-secondary')
