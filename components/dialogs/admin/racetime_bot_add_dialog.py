"""
RacetimeBotAddDialog component for adding new RaceTime bots.

This dialog belongs to the presentation layer and delegates all business logic
to services in application/services.
"""

from __future__ import annotations
from typing import Optional, Callable
from nicegui import ui
from models import User
from application.services.racetime.racetime_bot_service import RacetimeBotService
from components.dialogs.common.base_dialog import BaseDialog
import logging

logger = logging.getLogger(__name__)


class RacetimeBotAddDialog(BaseDialog):
    """Dialog for adding new RaceTime bots."""

    def __init__(
        self,
        current_user: User,
        on_save: Optional[Callable] = None,
    ):
        """
        Initialize bot add dialog.

        Args:
            current_user: Currently logged in user
            on_save: Callback to execute after successful save
        """
        super().__init__()
        self.current_user = current_user
        self.on_save = on_save
        self.bot_service = RacetimeBotService()

        # Form state
        self.category = ""
        self.client_id = ""
        self.client_secret = ""
        self.name = ""
        self.description = ""
        self.handler_class = "SahaRaceHandler"
        self.is_active = True

    async def show(self) -> None:
        """Display the add dialog using BaseDialog structure."""
        self.create_dialog(
            title="Add RaceTime Bot",
            icon="add",
        )
        await super().show()

    def _render_body(self) -> None:
        """Render the dialog body content."""
        with ui.column().classes("full-width gap-md"):
            # Instructions
            with ui.row().classes("items-center gap-2 p-3 rounded bg-info text-white"):
                ui.icon("info")
                ui.label(
                    "Create a new RaceTime.gg bot configuration. You will need OAuth2 credentials from RaceTime.gg."
                )

            # Form fields
            with self.create_form_grid(columns=2):
                with ui.element("div"):
                    category_input = ui.input(
                        label="Category *", placeholder="e.g., alttpr, smz3"
                    ).classes("w-full")
                    category_input.on(
                        "update:model-value",
                        lambda e: setattr(self, "category", e.args.strip()),
                    )

                with ui.element("div"):
                    name_input = ui.input(
                        label="Name *", placeholder="Friendly name for this bot"
                    ).classes("w-full")
                    name_input.on(
                        "update:model-value",
                        lambda e: setattr(self, "name", e.args.strip()),
                    )

            with self.create_form_grid(columns=1):
                with ui.element("div"):
                    client_id_input = ui.input(
                        label="Client ID *",
                        placeholder="OAuth2 client ID from RaceTime.gg",
                    ).classes("w-full")
                    client_id_input.on(
                        "update:model-value",
                        lambda e: setattr(self, "client_id", e.args.strip()),
                    )

                with ui.element("div"):
                    client_secret_input = ui.input(
                        label="Client Secret *",
                        placeholder="OAuth2 client secret from RaceTime.gg",
                        password=True,
                        password_toggle_button=True,
                    ).classes("w-full")
                    client_secret_input.on(
                        "update:model-value",
                        lambda e: setattr(self, "client_secret", e.args.strip()),
                    )

                with ui.element("div"):
                    description_input = ui.textarea(
                        label="Description", placeholder="Optional description"
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

            handler_options = [
                "SahaRaceHandler",
                "ALTTPRRaceHandler",
                "SMRaceHandler",
                "SMZ3RaceHandler",
                "AsyncLiveRaceHandler",
            ]
            handler_select = ui.select(
                options=handler_options,
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
                ui.button("Create Bot", on_click=self._save_and_close).classes(
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

        try:
            # Create bot via service
            bot = await self.bot_service.create_bot(
                category=self.category,
                client_id=self.client_id,
                client_secret=self.client_secret,
                name=self.name,
                description=self.description if self.description else None,
                handler_class=self.handler_class,
                is_active=self.is_active,
                current_user=self.current_user,
            )

            if bot:
                ui.notify(
                    f'RaceTime bot "{bot.name}" created successfully', type="positive"
                )
                if self.on_save:
                    await self.on_save()
                await self.close()
            else:
                ui.notify("Failed to create bot (permission denied)", type="negative")

        except ValueError as e:
            ui.notify(str(e), type="negative")
        except Exception as e:
            logger.error("Error creating RaceTime bot: %s", e, exc_info=True)
            ui.notify("An error occurred while creating the bot", type="negative")
