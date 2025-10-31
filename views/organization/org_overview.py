"""
Organization Overview view.

Displays summary information and stats for an organization.
"""

from __future__ import annotations
from typing import Any
from nicegui import ui
from models import Organization
from components.card import Card
from components.datetime_label import DateTimeLabel


class OrganizationOverviewView:
    """Overview dashboard for an organization."""

    def __init__(self, organization: Organization, user: Any) -> None:
        self.organization = organization
        self.user = user

    async def render(self) -> None:
        """Render the organization overview."""
        # Welcome card
        with Card.create(title='Organization Overview'):
            with ui.column().classes('gap-md'):
                ui.label(f'Welcome to {self.organization.name}').classes('text-xl')
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
        
        # Stats cards (placeholder for future metrics)
        with ui.row().classes('w-full gap-md mt-2'):
            with Card.create(title='Members', classes='flex-1'):
                ui.label('0').classes('text-4xl font-bold')
                ui.label('Total members').classes('text-secondary')
            
            with Card.create(title='Activity', classes='flex-1'):
                ui.label('0').classes('text-4xl font-bold')
                ui.label('Recent actions').classes('text-secondary')
            
            with Card.create(title='Resources', classes='flex-1'):
                ui.label('0').classes('text-4xl font-bold')
                ui.label('Total items').classes('text-secondary')
