"""
User Profile Settings view.

Allows users to edit their display name, pronouns, and other profile preferences.
"""

from __future__ import annotations
import logging
from nicegui import ui
from models import User
from components.card import Card
from application.services.user_service import UserService

logger = logging.getLogger(__name__)


class ProfileSettingsView:
    """View for editing user profile settings."""

    def __init__(self, user: User) -> None:
        self.user = user
        self.service = UserService()
        self.container = None

    async def _refresh(self) -> None:
        """Refresh the view."""
        if self.container:
            self.container.clear()
            with self.container:
                await self._render_content()

    async def _render_content(self) -> None:
        """Render the settings form."""
        # Input fields
        display_name_input = ui.input(
            label='Display Name',
            placeholder='Leave empty to use Discord username',
            value=self.user.display_name or ''
        ).classes('w-full')
        display_name_input.tooltip('This name will be shown throughout the application')

        pronouns_input = ui.input(
            label='Pronouns',
            placeholder='e.g., they/them, she/her, he/him',
            value=self.user.pronouns or ''
        ).classes('w-full')

        show_pronouns_checkbox = ui.checkbox(
            'Display pronouns after my name',
            value=self.user.show_pronouns
        ).classes('mt-2')
        show_pronouns_checkbox.tooltip('When enabled, your pronouns will appear in italics after your name')

        ui.separator().classes('my-4')

        # Email section
        ui.label('Email Address').classes('font-semibold text-lg')
        ui.label('Set your email address for notifications and account recovery.').classes('text-sm text-secondary mb-2')

        email_input = ui.input(
            label='Email',
            placeholder='your.email@example.com',
            value=self.user.email or ''
        ).classes('w-full')

        # Show verification status
        if self.user.email:
            if self.user.email_verified:
                with ui.row().classes('items-center gap-2 text-sm text-success'):
                    ui.icon('verified').classes('text-lg')
                    ui.label('Email verified')
            else:
                with ui.row().classes('items-center gap-2 text-sm text-warning'):
                    ui.icon('warning').classes('text-lg')
                    ui.label('Email not verified')

        # Warning about auto-verification
        with ui.element('div').classes('p-3 rounded bg-warning-light mt-2'):
            with ui.row().classes('items-start gap-2'):
                ui.icon('info').classes('text-warning')
                with ui.column().classes('flex-1'):
                    ui.label('Email Verification Notice').classes('font-semibold text-sm')
                    ui.label('Email verification is currently disabled. Email addresses are automatically approved for development purposes. See SECURITY.md for details.').classes('text-xs text-secondary')

        # Preview section
        ui.separator()
        ui.label('Preview').classes('font-semibold mt-4')

        preview_container = ui.element('div').classes('p-4 rounded bg-surface-color')

        def update_preview():
            """Update the preview display."""
            preview_container.clear()
            with preview_container:
                # Calculate what would be shown
                display = display_name_input.value.strip() if display_name_input.value.strip() else self.user.discord_username
                pronouns_value = pronouns_input.value.strip()

                if show_pronouns_checkbox.value and pronouns_value:
                    with ui.row().classes('items-center gap-2'):
                        ui.label(display).classes('font-bold')
                        ui.label(f'({pronouns_value})').classes('text-secondary italic')
                else:
                    ui.label(display).classes('font-bold')

        # Update preview when inputs change
        display_name_input.on('input', update_preview)
        pronouns_input.on('input', update_preview)
        show_pronouns_checkbox.on('change', update_preview)

        # Initial preview
        update_preview()

        ui.separator()

        async def save_settings():
            """Save profile settings."""
            try:
                # Get values
                display_name = display_name_input.value.strip() if display_name_input.value else None
                pronouns = pronouns_input.value.strip() if pronouns_input.value else None
                show_pronouns = show_pronouns_checkbox.value
                email = email_input.value.strip() if email_input.value else None

                # Update profile via service
                await self.service.update_user_profile(
                    user=self.user,
                    display_name=display_name,
                    pronouns=pronouns,
                    show_pronouns=show_pronouns
                )

                # Update email via service
                await self.service.update_user_email(
                    user=self.user,
                    email=email
                )

                ui.notify('Profile settings saved', type='positive')
                await self._refresh()
            except ValueError as e:
                # Handle validation errors (e.g., invalid email format)
                logger.error("Validation error saving profile settings: %s", e)
                ui.notify(f'Validation error: {str(e)}', type='warning')
            except Exception as e:
                # Handle any other unexpected errors
                logger.error("Failed to save profile settings: %s", e)
                ui.notify(f'Failed to save settings: {str(e)}', type='negative')

        # Action buttons
        with ui.row().classes('gap-2 mt-4'):
            ui.button('Save Changes', on_click=save_settings).classes('btn btn-primary').props('icon=save')

    async def render(self) -> None:
        """Render the profile settings view."""
        with Card.create(title='Profile Settings'):
            self.container = ui.element('div').classes('flex flex-col gap-4')
            with self.container:
                await self._render_content()
