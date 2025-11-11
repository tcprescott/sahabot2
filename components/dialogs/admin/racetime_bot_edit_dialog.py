"""
RacetimeBotEditDialog component for editing existing RaceTime bots.

This dialog belongs to the presentation layer and delegates all business logic
to services in application/services.
"""

from __future__ import annotations
from typing import Optional, Callable
from nicegui import ui
from models import User, RacetimeBot
from application.services.racetime.racetime_bot_service import RacetimeBotService
from components.dialogs.common.base_dialog import BaseDialog
from racetime import AVAILABLE_HANDLER_CLASSES
import logging

logger = logging.getLogger(__name__)


class RacetimeBotEditDialog(BaseDialog):
    """Dialog for editing existing RaceTime bots."""

    def __init__(
        self,
        bot: RacetimeBot,
        current_user: User,
        on_save: Optional[Callable] = None,
    ):
        """
        Initialize bot edit dialog.

        Args:
            bot: Bot to edit
            current_user: Currently logged in user
            on_save: Callback to execute after successful save
        """
        super().__init__()
        self.bot = bot
        self.current_user = current_user
        self.on_save = on_save
        self.bot_service = RacetimeBotService()

        # Form state (initialize with current values)
        self.category = bot.category
        self.client_id = bot.client_id
        self.client_secret = bot.client_secret
        self.name = bot.name
        self.description = bot.description or ""
        self.handler_class = bot.handler_class
        self.is_active = bot.is_active

    async def show(self) -> None:
        """Display the edit dialog using BaseDialog structure."""
        self.create_dialog(
            title=f"Edit RaceTime Bot: {self.bot.name}",
            icon="edit",
        )
        await super().show()

    def _render_body(self) -> None:
        """Render the dialog body content."""
        with ui.column().classes("full-width gap-md"):
            # Bot info
            self.create_section_title("Bot Information")
            self.create_info_row("ID", str(self.bot.id))

            ui.separator()

            # Editable fields
            self.create_section_title("Configuration")
            with self.create_form_grid(columns=2):
                with ui.element("div"):
                    category_input = ui.input(
                        label="Category *", value=self.category
                    ).classes("w-full")
                    category_input.on(
                        "update:model-value",
                        lambda e: setattr(self, "category", e.args.strip()),
                    )

                with ui.element("div"):
                    name_input = ui.input(label="Name *", value=self.name).classes(
                        "w-full"
                    )
                    name_input.on(
                        "update:model-value",
                        lambda e: setattr(self, "name", e.args.strip()),
                    )

            with self.create_form_grid(columns=1):
                with ui.element("div"):
                    client_id_input = ui.input(
                        label="Client ID *", value=self.client_id
                    ).classes("w-full")
                    client_id_input.on(
                        "update:model-value",
                        lambda e: setattr(self, "client_id", e.args.strip()),
                    )

                with ui.element("div"):
                    client_secret_input = ui.input(
                        label="Client Secret *",
                        value=self.client_secret,
                        password=True,
                        password_toggle_button=True,
                    ).classes("w-full")
                    client_secret_input.on(
                        "update:model-value",
                        lambda e: setattr(self, "client_secret", e.args.strip()),
                    )

                with ui.element("div"):
                    description_input = ui.textarea(
                        label="Description", value=self.description
                    ).classes("w-full")
                    description_input.on(
                        "update:model-value",
                        lambda e: setattr(self, "description", e.args.strip()),
                    )

            # Handler class selection
            with ui.row().classes("full-width items-center gap-2"):
                ui.label("Handler Class *").classes("font-medium")
                ui.icon("info").classes("text-grey-7").tooltip(
                    "The Python handler class that provides race room commands and behavior. "
                    "Choose a category-specific handler (e.g., ALTTPRRaceHandler) or use the default SahaRaceHandler."
                )

            handler_select = ui.select(
                options=AVAILABLE_HANDLER_CLASSES,
                value=self.handler_class,
                label="Handler",
            ).classes("w-full")
            handler_select.on(
                "update:model-value",
                lambda e: setattr(self, "handler_class", e.args),
            )

            # Active status
            status_checkbox = ui.checkbox("Active", value=self.is_active)
            status_checkbox.on(
                "update:model-value",
                lambda e: setattr(
                    self, "is_active", e.args[0] if isinstance(e.args, list) else e.args
                ),
            )

            ui.separator()

            # Actions
            with self.create_actions_row():
                ui.button("Cancel", on_click=self.close).classes("btn")
                ui.button("Save Changes", on_click=self._save_and_close).classes(
                    "btn"
                ).props("color=positive")

    async def _save_and_close(self) -> None:
        """Validate, save, and close dialog."""
        # Validate required fields
        if (
            not self.category
            or not self.client_id
            or not self.client_secret
            or not self.name
        ):
            ui.notify("Please fill in all required fields", type="negative")
            return

        # Detect changes
        updates = {}
        if self.category != self.bot.category:
            updates["category"] = self.category
        if self.client_id != self.bot.client_id:
            updates["client_id"] = self.client_id
        if self.client_secret != self.bot.client_secret:
            updates["client_secret"] = self.client_secret
        if self.name != self.bot.name:
            updates["name"] = self.name
        if self.description != (self.bot.description or ""):
            updates["description"] = self.description if self.description else None
        if self.handler_class != self.bot.handler_class:
            updates["handler_class"] = self.handler_class
        if self.is_active != self.bot.is_active:
            updates["is_active"] = self.is_active

        if not updates:
            ui.notify("No changes to save", type="info")
            await self.close()
            return

        try:
            # Update bot via service
            bot = await self.bot_service.update_bot(
                self.bot.id, self.current_user, **updates
            )

            if bot:
                ui.notify(
                    f'RaceTime bot "{bot.name}" updated successfully', type="positive"
                )
                if self.on_save:
                    await self.on_save()
                await self.close()
            else:
                ui.notify("Failed to update bot (permission denied)", type="negative")

        except ValueError as e:
            ui.notify(str(e), type="negative")
        except Exception as e:
            logger.error("Error updating RaceTime bot: %s", e, exc_info=True)
            ui.notify("An error occurred while updating the bot", type="negative")
