"""
Race room profile management dialog.

Displays a table of profiles with create/edit/delete/set default actions.
"""

from nicegui import ui
from models import User
from components.dialogs.common.base_dialog import BaseDialog


class RaceRoomProfileDialog(BaseDialog):
    """Dialog for creating/editing race room profiles."""

    def __init__(self, user: User, organization_id: int, profile=None, on_save=None):
        """
        Initialize the profile dialog.

        Args:
            user: Current user
            organization_id: Organization ID
            profile: Existing profile to edit (None for create)
            on_save: Callback after successful save
        """
        super().__init__()
        self.user = user
        self.organization_id = organization_id
        self.profile = profile
        self.on_save = on_save
        self.is_editing = profile is not None

        # Form fields
        self.name_input = None
        self.description_input = None
        self.start_delay_input = None
        self.time_limit_input = None
        self.streaming_required_switch = None
        self.auto_start_switch = None
        self.allow_comments_switch = None
        self.hide_comments_switch = None
        self.allow_prerace_chat_switch = None
        self.allow_midrace_chat_switch = None
        self.allow_non_entrant_chat_switch = None
        self.is_default_switch = None

    async def show(self):
        """Display the dialog."""
        title = (
            f"Edit Profile: {self.profile.name}"
            if self.is_editing
            else "Create Race Room Profile"
        )
        self.create_dialog(
            title=title,
            icon="tune" if self.is_editing else "add_circle",
            max_width="800px",
        )
        await super().show()

    def _render_body(self):
        """Render dialog content."""
        # Basic Info Section
        self.create_section_title("Basic Information")

        with self.create_form_grid(columns=1):
            with ui.element("div"):
                self.name_input = ui.input(
                    label="Profile Name",
                    value=self.profile.name if self.is_editing else "",
                    placeholder="e.g., Standard, Speedrun, Casual",
                ).classes("w-full")

            with ui.element("div"):
                self.description_input = ui.textarea(
                    label="Description (Optional)",
                    value=self.profile.description if self.is_editing else "",
                    placeholder="Brief description of this profile",
                ).classes("w-full")

        ui.separator()

        # Race Timing Section
        self.create_section_title("Race Timing")

        with self.create_form_grid(columns=2):
            with ui.element("div"):
                self.start_delay_input = ui.number(
                    label="Start Countdown (seconds)",
                    value=self.profile.start_delay if self.is_editing else 15,
                    min=10,
                    max=60,
                    step=5,
                ).classes("w-full")
                ui.label("Countdown timer before race starts").classes(
                    "text-sm text-grey"
                )

            with ui.element("div"):
                self.time_limit_input = ui.number(
                    label="Time Limit (hours)",
                    value=self.profile.time_limit if self.is_editing else 24,
                    min=1,
                    max=72,
                    step=1,
                ).classes("w-full")
                ui.label("Maximum time allowed for race").classes("text-sm text-grey")

        ui.separator()

        # Stream & Automation Section
        self.create_section_title("Stream & Automation")

        with self.create_form_grid(columns=2):
            with ui.element("div"):
                with ui.row().classes("items-center gap-2"):
                    self.streaming_required_switch = ui.checkbox(
                        value=(
                            self.profile.streaming_required
                            if self.is_editing
                            else False
                        )
                    )
                    ui.label("Require Streaming")
                ui.label("All participants must be streaming").classes(
                    "text-sm text-grey"
                )

            with ui.element("div"):
                with ui.row().classes("items-center gap-2"):
                    self.auto_start_switch = ui.checkbox(
                        value=self.profile.auto_start if self.is_editing else True
                    )
                    ui.label("Auto-start When Ready")
                ui.label("Start automatically when all racers ready").classes(
                    "text-sm text-grey"
                )

        ui.separator()

        # Chat Permissions Section
        self.create_section_title("Chat Permissions")

        with self.create_form_grid(columns=2):
            with ui.element("div"):
                with ui.row().classes("items-center gap-2"):
                    self.allow_comments_switch = ui.checkbox(
                        value=self.profile.allow_comments if self.is_editing else True
                    )
                    ui.label("Allow Race Comments")
                ui.label("Racers can leave comments on the race").classes(
                    "text-sm text-grey"
                )

            with ui.element("div"):
                with ui.row().classes("items-center gap-2"):
                    self.hide_comments_switch = ui.checkbox(
                        value=self.profile.hide_comments if self.is_editing else False
                    )
                    ui.label("Hide Comments Until Finish")
                ui.label("Comments hidden until race ends").classes("text-sm text-grey")

            with ui.element("div"):
                with ui.row().classes("items-center gap-2"):
                    self.allow_prerace_chat_switch = ui.checkbox(
                        value=(
                            self.profile.allow_prerace_chat if self.is_editing else True
                        )
                    )
                    ui.label("Pre-race Chat")
                ui.label("Chat enabled before race starts").classes("text-sm text-grey")

            with ui.element("div"):
                with ui.row().classes("items-center gap-2"):
                    self.allow_midrace_chat_switch = ui.checkbox(
                        value=(
                            self.profile.allow_midrace_chat if self.is_editing else True
                        )
                    )
                    ui.label("Mid-race Chat")
                ui.label("Chat enabled during the race").classes("text-sm text-grey")

            with ui.element("div"):
                with ui.row().classes("items-center gap-2"):
                    self.allow_non_entrant_chat_switch = ui.checkbox(
                        value=(
                            self.profile.allow_non_entrant_chat
                            if self.is_editing
                            else True
                        )
                    )
                    ui.label("Non-entrant Chat")
                ui.label("Spectators can chat in the room").classes("text-sm text-grey")

        ui.separator()

        # Default Profile Section
        self.create_section_title("Default Profile")

        with ui.row().classes("items-center gap-2 w-full"):
            self.is_default_switch = ui.checkbox(
                value=self.profile.is_default if self.is_editing else False
            )
            ui.label("Set as default profile for this organization")

        ui.separator()

        # Action buttons
        with self.create_actions_row():
            ui.button("Cancel", on_click=self.close).classes("btn")
            ui.button("Save Profile", on_click=self._save, icon="save").classes(
                "btn"
            ).props("color=positive")

    async def _save(self):
        """Save the profile."""
        from application.services.racetime.race_room_profile_service import (
            RaceRoomProfileService,
        )

        # Validate
        if not self.name_input.value or not self.name_input.value.strip():
            ui.notify("Profile name is required", type="negative")
            return

        service = RaceRoomProfileService()

        try:
            if self.is_editing:
                # Update existing profile
                profile = await service.update_profile(
                    current_user=self.user,
                    organization_id=self.organization_id,
                    profile_id=self.profile.id,
                    name=self.name_input.value.strip(),
                    description=(
                        self.description_input.value.strip()
                        if self.description_input.value
                        else ""
                    ),
                    start_delay=int(self.start_delay_input.value),
                    time_limit=int(self.time_limit_input.value),
                    streaming_required=self.streaming_required_switch.value,
                    auto_start=self.auto_start_switch.value,
                    allow_comments=self.allow_comments_switch.value,
                    hide_comments=self.hide_comments_switch.value,
                    allow_prerace_chat=self.allow_prerace_chat_switch.value,
                    allow_midrace_chat=self.allow_midrace_chat_switch.value,
                    allow_non_entrant_chat=self.allow_non_entrant_chat_switch.value,
                    is_default=self.is_default_switch.value,
                )
                message = f"Profile '{profile.name}' updated successfully!"
            else:
                # Create new profile
                profile = await service.create_profile(
                    current_user=self.user,
                    organization_id=self.organization_id,
                    name=self.name_input.value.strip(),
                    description=(
                        self.description_input.value.strip()
                        if self.description_input.value
                        else ""
                    ),
                    start_delay=int(self.start_delay_input.value),
                    time_limit=int(self.time_limit_input.value),
                    streaming_required=self.streaming_required_switch.value,
                    auto_start=self.auto_start_switch.value,
                    allow_comments=self.allow_comments_switch.value,
                    hide_comments=self.hide_comments_switch.value,
                    allow_prerace_chat=self.allow_prerace_chat_switch.value,
                    allow_midrace_chat=self.allow_midrace_chat_switch.value,
                    allow_non_entrant_chat=self.allow_non_entrant_chat_switch.value,
                    is_default=self.is_default_switch.value,
                )
                message = f"Profile '{profile.name}' created successfully!"

            if profile:
                ui.notify(message, type="positive")
                if self.on_save:
                    await self.on_save()
                await self.close()
            else:
                ui.notify("Permission denied or operation failed", type="negative")

        except Exception as e:
            ui.notify(f"Error: {str(e)}", type="negative")
