"""
User Profile Information view.

Display and edit user's basic profile information.
"""

from __future__ import annotations
from nicegui import ui
from models import User
from components.card import Card
from components.badge import Badge
from components.datetime_label import DateTimeLabel


class ProfileInfoView:
    """View for displaying user profile information."""

    def __init__(self, user: User) -> None:
        self.user = user

    async def render(self) -> None:
        """Render the profile information."""
        with Card.create(title='Profile Information'):
            with ui.element('div').classes('flex flex-col gap-4'):
                # Discord Username
                with ui.row().classes('items-center'):
                    ui.icon('badge').classes('text-secondary')
                    with ui.column().classes('flex-1'):
                        ui.label('Discord Username').classes('text-sm text-secondary')
                        ui.label(self.user.get_display_name()).classes('font-bold')

                # Discord ID
                with ui.row().classes('items-center'):
                    ui.icon('fingerprint').classes('text-secondary')
                    with ui.column().classes('flex-1'):
                        ui.label('Discord ID').classes('text-sm text-secondary')
                        ui.label(str(self.user.discord_id)).classes('font-mono')

                # Email (only show to superadmin or self)
                if self.user.discord_email:
                    with ui.row().classes('items-center'):
                        ui.icon('email').classes('text-secondary')
                        with ui.column().classes('flex-1'):
                            ui.label('Email').classes('text-sm text-secondary')
                            ui.label(self.user.discord_email).classes('font-mono')

                # Permission Level
                with ui.row().classes('items-center'):
                    ui.icon('security').classes('text-secondary')
                    with ui.column().classes('flex-1'):
                        ui.label('Permission Level').classes('text-sm text-secondary')
                        Badge.permission(self.user.permission)

                # Account Status
                with ui.row().classes('items-center'):
                    ui.icon('verified' if self.user.is_active else 'block').classes('text-secondary')
                    with ui.column().classes('flex-1'):
                        ui.label('Account Status').classes('text-sm text-secondary')
                        Badge.status(self.user.is_active)

                # Member Since
                with ui.row().classes('items-center'):
                    ui.icon('calendar_today').classes('text-secondary')
                    with ui.column().classes('flex-1'):
                        ui.label('Member Since').classes('text-sm text-secondary')
                        DateTimeLabel.date(self.user.created_at, classes='text-sm')
