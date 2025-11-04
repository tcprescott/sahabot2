"""
Dialog for adding/editing racetime chat commands.

This dialog supports creating and editing commands for:
- BOT scope (global bot-level commands)
- TOURNAMENT scope (tournament-specific commands)
- ASYNC_TOURNAMENT scope (async tournament-specific commands)
"""

from __future__ import annotations
from typing import Callable, Optional
from nicegui import ui
from components.dialogs.common.base_dialog import BaseDialog
from models import RacetimeChatCommand, CommandScope, CommandResponseType
from racetime.command_handlers import BUILTIN_HANDLERS
import logging

logger = logging.getLogger(__name__)


class RacetimeChatCommandDialog(BaseDialog):
    """Dialog for adding or editing a racetime chat command."""

    def __init__(
        self,
        command: Optional[RacetimeChatCommand] = None,
        bot_id: Optional[int] = None,
        tournament_id: Optional[int] = None,
        async_tournament_id: Optional[int] = None,
        on_save: Optional[Callable] = None,
    ):
        """
        Initialize the racetime chat command dialog.

        Args:
            command: Existing command to edit (None for new command)
            bot_id: RaceTime bot ID (for BOT scope)
            tournament_id: Tournament ID (for TOURNAMENT scope)
            async_tournament_id: Async tournament ID (for ASYNC_TOURNAMENT scope)
            on_save: Callback function after successful save
        """
        super().__init__()
        self.command = command
        self.bot_id = bot_id
        self.tournament_id = tournament_id
        self.async_tournament_id = async_tournament_id
        self.on_save = on_save

        # Determine scope based on context
        if self.command:
            if self.command.bot_id:
                self.scope = CommandScope.BOT
            elif self.command.tournament_id:
                self.scope = CommandScope.TOURNAMENT
            elif self.command.async_tournament_id:
                self.scope = CommandScope.ASYNC_TOURNAMENT
        elif bot_id:
            self.scope = CommandScope.BOT
        elif tournament_id:
            self.scope = CommandScope.TOURNAMENT
        elif async_tournament_id:
            self.scope = CommandScope.ASYNC_TOURNAMENT
        else:
            raise ValueError("Must provide bot_id, tournament_id, or async_tournament_id")

        # UI elements
        self.command_input: Optional[ui.input] = None
        self.response_type_select: Optional[ui.select] = None
        self.response_text_area: Optional[ui.textarea] = None
        self.handler_select: Optional[ui.select] = None
        self.cooldown_seconds_input: Optional[ui.number] = None
        self.require_linked_account_checkbox: Optional[ui.checkbox] = None
        self.is_enabled_checkbox: Optional[ui.checkbox] = None
        self.error_label: Optional[ui.label] = None

    async def show(self):
        """Display the dialog."""
        title = 'Edit Chat Command' if self.command else 'Add Chat Command'
        icon = 'edit' if self.command else 'add'

        self.create_dialog(
            title=title,
            icon=icon,
            max_width='600px'
        )
        await super().show()

    def _render_body(self):
        """Render the dialog content."""
        # Command name
        self.create_section_title('Command Details')
        with ui.row().classes('w-full gap-2 items-center'):
            ui.label('!').classes('text-2xl font-bold')
            self.command_input = ui.input(
                label='Command Name',
                placeholder='help, status, rules...',
                value=self.command.command if self.command else ''
            ).classes('flex-grow').props('outlined dense')
            if self.command:
                self.command_input.props('readonly')

        ui.label('Command name without the ! prefix. Lowercase, no spaces.').classes('text-sm text-secondary mt-1')

        ui.separator()

        # Response type
        self.create_section_title('Response Configuration')
        response_types = {
            'Static Text': CommandResponseType.TEXT.value,
            'Dynamic Handler': CommandResponseType.DYNAMIC.value,
        }
        self.response_type_select = ui.select(
            label='Response Type',
            options=response_types,
            value=self.command.response_type.value if self.command else CommandResponseType.TEXT.value,
            on_change=self._on_response_type_change
        ).classes('w-full').props('outlined dense')

        # Response text (for TEXT type)
        self.response_text_area = ui.textarea(
            label='Response Text',
            placeholder='Enter the text to send when this command is used...',
            value=self.command.response_text if self.command else ''
        ).classes('w-full').props('outlined dense rows=4')

        # Handler selection (for DYNAMIC type)
        handler_options = {
            name: name for name in BUILTIN_HANDLERS.keys()
        }
        self.handler_select = ui.select(
            label='Handler Function',
            options=handler_options,
            value=self.command.handler_name if self.command else None,
        ).classes('w-full').props('outlined dense')

        # Show/hide based on response type
        self._on_response_type_change(None)

        ui.separator()

        # Settings
        self.create_section_title('Settings')

        with self.create_form_grid(columns=2):
            with ui.element('div'):
                self.cooldown_seconds_input = ui.number(
                    label='Cooldown (seconds)',
                    value=self.command.cooldown_seconds if self.command else 0,
                    min=0,
                    max=3600,
                    step=1,
                ).classes('w-full').props('outlined dense')
                ui.label('Minimum time between command uses (0 = no cooldown)').classes('text-xs text-secondary mt-1')

            with ui.element('div'):
                self.require_linked_account_checkbox = ui.checkbox(
                    'Require Linked Account',
                    value=self.command.require_linked_account if self.command else False
                )
                ui.label('Only users with linked racetime accounts can use').classes('text-xs text-secondary mt-1')

        self.is_enabled_checkbox = ui.checkbox(
            'Enabled',
            value=self.command.is_enabled if self.command else True
        )
        ui.label('Disable to temporarily turn off this command without deleting it').classes('text-xs text-secondary mt-1')

        # Error message container
        self.error_label = ui.label('').classes('text-negative hidden')

        ui.separator()

        # Actions
        with self.create_actions_row():
            ui.button('Cancel', on_click=self.close).classes('btn')
            ui.button(
                'Save' if self.command else 'Add',
                on_click=self._save
            ).classes('btn').props('color=positive')

    def _on_response_type_change(self, _):
        """Handle response type selection change."""
        if not self.response_type_select or not self.response_text_area or not self.handler_select:
            return

        response_type = self.response_type_select.value
        if response_type == CommandResponseType.TEXT.value:
            self.response_text_area.set_visibility(True)
            self.handler_select.set_visibility(False)
        else:  # DYNAMIC
            self.response_text_area.set_visibility(False)
            self.handler_select.set_visibility(True)

    async def _save(self):
        """Save the command."""
        # Validate inputs
        command_name = self.command_input.value.strip().lower() if self.command_input else ''
        if not command_name:
            self.error_label.text = 'Command name is required'
            self.error_label.classes(remove='hidden')
            return

        # Validate command name format (alphanumeric and underscore only)
        if not command_name.replace('_', '').isalnum():
            self.error_label.text = 'Command name can only contain letters, numbers, and underscores'
            self.error_label.classes(remove='hidden')
            return

        response_type = CommandResponseType(self.response_type_select.value) if self.response_type_select else CommandResponseType.TEXT

        # Validate response configuration
        if response_type == CommandResponseType.TEXT:
            response_text = self.response_text_area.value.strip() if self.response_text_area else ''
            if not response_text:
                self.error_label.text = 'Response text is required for static text commands'
                self.error_label.classes(remove='hidden')
                return
            handler_name = None
        else:  # DYNAMIC
            handler_name = self.handler_select.value if self.handler_select else None
            if not handler_name:
                self.error_label.text = 'Handler function is required for dynamic commands'
                self.error_label.classes(remove='hidden')
                return
            response_text = None

        # Prepare command data
        command_data = {
            'command': command_name,
            'scope': self.scope,
            'response_type': response_type,
            'response_text': response_text,
            'handler_name': handler_name,
            'require_linked_account': self.require_linked_account_checkbox.value if self.require_linked_account_checkbox else False,
            'cooldown_seconds': int(self.cooldown_seconds_input.value or 0) if self.cooldown_seconds_input else 0,
            'is_active': self.is_enabled_checkbox.value if self.is_enabled_checkbox else True,
        }

        # Set scope-specific ID
        if self.scope == CommandScope.BOT:
            command_data['bot_id'] = self.bot_id
        elif self.scope == CommandScope.TOURNAMENT:
            command_data['tournament_id'] = self.tournament_id
        elif self.scope == CommandScope.ASYNC_TOURNAMENT:
            command_data['async_tournament_id'] = self.async_tournament_id

        try:
            # Import service
            from application.services.racetime_chat_command_service import RacetimeChatCommandService
            from middleware.auth import DiscordAuthService
            service = RacetimeChatCommandService()
            user = await DiscordAuthService.get_current_user()

            if self.command:
                # Update existing command
                await service.update_command(user, self.command.id, **command_data)
                ui.notify('Command updated successfully', color='positive')
            else:
                # Create new command
                await service.create_command(user, **command_data)
                ui.notify('Command created successfully', color='positive')

            # Callback and close
            if self.on_save:
                await self.on_save()
            await self.close()

        except ValueError as e:
            self.error_label.text = str(e)
            self.error_label.classes(remove='hidden')
            logger.error("Error saving command: %s", e)
        except Exception as e:
            self.error_label.text = f'Error saving command: {str(e)}'
            self.error_label.classes(remove='hidden')
            logger.error("Unexpected error saving command: %s", e, exc_info=True)
