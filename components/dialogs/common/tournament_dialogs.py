"""Dialogs for creating and editing Tournaments."""

from __future__ import annotations
from typing import Optional, Callable
from nicegui import ui
from components.dialogs.common.base_dialog import BaseDialog
import logging

logger = logging.getLogger(__name__)


class TournamentDialog(BaseDialog):
    """Dialog for creating or editing a tournament."""

    def __init__(
        self,
        *,
        title: str,
        initial_name: str = "",
        initial_description: Optional[str] = None,
        initial_is_active: bool = True,
        initial_tracker_enabled: bool = True,
        # RaceTime settings
        available_racetime_bots: Optional[dict[int, str]] = None,
        initial_racetime_bot_id: Optional[int] = None,
        initial_racetime_auto_create: bool = False,
        initial_room_open_minutes: int = 60,
        initial_require_racetime_link: bool = False,
        initial_racetime_default_goal: Optional[str] = None,
        on_submit: Optional[Callable] = None,
    ) -> None:
        super().__init__()
        self._title = title
        self._initial_name = initial_name
        self._initial_description = initial_description
        self._initial_is_active = initial_is_active
        self._initial_tracker_enabled = initial_tracker_enabled
        self._on_submit = on_submit
        
        # RaceTime settings
        self._available_racetime_bots = available_racetime_bots or {}
        self._initial_racetime_bot_id = initial_racetime_bot_id
        self._initial_racetime_auto_create = initial_racetime_auto_create
        self._initial_room_open_minutes = initial_room_open_minutes
        self._initial_require_racetime_link = initial_require_racetime_link
        self._initial_racetime_default_goal = initial_racetime_default_goal

        # UI refs
        self._name_input: Optional[ui.input] = None
        self._desc_input: Optional[ui.textarea] = None
        self._active_toggle: Optional[ui.switch] = None
        self._tracker_toggle: Optional[ui.switch] = None
        
        # RaceTime UI refs
        self._racetime_bot_select: Optional[ui.select] = None
        self._racetime_auto_create_toggle: Optional[ui.switch] = None
        self._room_open_minutes_input: Optional[ui.number] = None
        self._require_racetime_link_toggle: Optional[ui.switch] = None
        self._racetime_default_goal_input: Optional[ui.input] = None

    async def show(self) -> None:
        """Display the dialog."""
        self.create_dialog(title=self._title, icon='emoji_events', max_width='800px')
        await super().show()

    def _render_body(self) -> None:
        """Render dialog body with form fields."""
        # Basic Settings Section
        self.create_section_title('Basic Settings')
        
        with self.create_form_grid(columns=1):
            with ui.element('div'):
                self._name_input = ui.input(label='Name', value=self._initial_name).classes('w-full')
            with ui.element('div'):
                self._desc_input = ui.textarea(label='Description', value=self._initial_description or "").classes('w-full')
            with ui.element('div'):
                self._active_toggle = ui.switch(text='Active', value=self._initial_is_active)
            with ui.element('div'):
                self._tracker_toggle = ui.switch(text='Enable Tracker Role', value=self._initial_tracker_enabled)

        ui.separator().classes('my-4')

        # RaceTime.gg Integration Section
        self.create_section_title('RaceTime.gg Integration')
        
        with ui.column().classes('gap-md w-full'):
            # Bot selection
            with ui.element('div'):
                bot_options = {None: '(No RaceTime integration)'}
                bot_options.update(self._available_racetime_bots)
                
                self._racetime_bot_select = ui.select(
                    label='RaceTime Bot',
                    options=bot_options,
                    value=self._initial_racetime_bot_id,
                    with_input=True,
                ).classes('w-full')
                ui.label('Select a RaceTime bot to enable automatic race room creation').classes('text-xs text-secondary mt-1')
            
            # Auto-create rooms toggle
            with ui.element('div'):
                self._racetime_auto_create_toggle = ui.switch(
                    text='Automatically create race rooms',
                    value=self._initial_racetime_auto_create
                )
                ui.label('When enabled, race rooms will be created automatically before scheduled matches').classes('text-xs text-secondary mt-1')
            
            # Room open time
            with ui.element('div'):
                self._room_open_minutes_input = ui.number(
                    label='Minutes before match to open room',
                    value=self._initial_room_open_minutes,
                    min=15,
                    max=240,
                    step=15,
                ).classes('w-full')
                ui.label('How long before the scheduled match time should the room be opened (15-240 minutes)').classes('text-xs text-secondary mt-1')
            
            # Require RaceTime link
            with ui.element('div'):
                self._require_racetime_link_toggle = ui.switch(
                    text='Require players to have RaceTime account linked',
                    value=self._initial_require_racetime_link
                )
                ui.label('When enabled, players must link their RaceTime account before scheduling matches').classes('text-xs text-secondary mt-1')
            
            # Default goal
            with ui.element('div'):
                self._racetime_default_goal_input = ui.input(
                    label='Default race goal (optional)',
                    value=self._initial_racetime_default_goal or '',
                    placeholder='e.g., Beat the game - Tournament'
                ).classes('w-full')
                ui.label('Default goal text for race rooms (can be overridden per-match)').classes('text-xs text-secondary mt-1')

        with self.create_actions_row():
            ui.button('Cancel', on_click=self.close).classes('btn')
            ui.button('Save', on_click=self._handle_submit).classes('btn').props('color=positive')

    async def _handle_submit(self) -> None:
        """Handle Save click and call callback."""
        if not self._name_input or not self._name_input.value:
            ui.notify('Name is required', type='warning')
            return
        
        name = self._name_input.value
        description = self._desc_input.value if self._desc_input else None
        is_active = bool(self._active_toggle.value) if self._active_toggle else True
        tracker_enabled = bool(self._tracker_toggle.value) if self._tracker_toggle else True
        
        # RaceTime settings
        racetime_bot_id = self._racetime_bot_select.value if self._racetime_bot_select else None
        racetime_auto_create = bool(self._racetime_auto_create_toggle.value) if self._racetime_auto_create_toggle else False
        room_open_minutes = int(self._room_open_minutes_input.value) if self._room_open_minutes_input else 60
        require_racetime_link = bool(self._require_racetime_link_toggle.value) if self._require_racetime_link_toggle else False
        racetime_default_goal = self._racetime_default_goal_input.value.strip() if self._racetime_default_goal_input and self._racetime_default_goal_input.value else None
        
        if self._on_submit:
            await self._on_submit(
                name=name,
                description=description,
                is_active=is_active,
                tracker_enabled=tracker_enabled,
                racetime_bot_id=racetime_bot_id,
                racetime_auto_create=racetime_auto_create,
                room_open_minutes=room_open_minutes,
                require_racetime_link=require_racetime_link,
                racetime_default_goal=racetime_default_goal,
            )
        await self.close()


class ConfirmDialog(BaseDialog):
    """Generic confirmation dialog with message and confirm action."""

    def __init__(self, title: str, message: str, on_confirm: Optional[Callable[[], None]] = None) -> None:
        super().__init__()
        self._title = title
        self._message = message
        self._on_confirm = on_confirm

    async def show(self) -> None:
        self.create_dialog(title=self._title, icon='help', max_width='dialog-card-sm')
        await super().show()

    def _render_body(self) -> None:
        ui.label(self._message).classes('mb-2')
        with self.create_actions_row():
            ui.button('Cancel', on_click=self.close).classes('btn')
            ui.button('Confirm', on_click=self._handle_confirm).classes('btn').props('color=negative')

    async def _handle_confirm(self) -> None:
        if self._on_confirm:
            await self._on_confirm()
        await self.close()
