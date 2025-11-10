"""
Twitch Account view for user profile.

Display and manage Twitch account linking.
"""

from __future__ import annotations
import logging
from nicegui import ui
from models import User
from components.card import Card

logger = logging.getLogger(__name__)


class TwitchAccountView:
    """View for managing Twitch account linking."""

    def __init__(self, user: User) -> None:
        self.user = user

    async def render(self) -> None:
        """Render the Twitch account management interface."""
        with Card.create(title="Twitch Account"):
            with ui.element("div").classes("flex flex-col gap-4"):
                # Account status
                if self.user.twitch_id:
                    # Account is linked
                    with ui.row().classes("items-center"):
                        ui.icon("link").classes("text-success")
                        with ui.column().classes("flex-1"):
                            ui.label("Account Status").classes("text-sm text-secondary")
                            ui.label("Linked").classes("badge badge-success")

                    # Twitch display name
                    with ui.row().classes("items-center"):
                        ui.icon("person").classes("text-secondary")
                        with ui.column().classes("flex-1"):
                            ui.label("Twitch Display Name").classes(
                                "text-sm text-secondary"
                            )
                            ui.label(
                                self.user.twitch_display_name or "Unknown"
                            ).classes("font-bold")

                    # Twitch username
                    with ui.row().classes("items-center"):
                        ui.icon("alternate_email").classes("text-secondary")
                        with ui.column().classes("flex-1"):
                            ui.label("Twitch Username").classes(
                                "text-sm text-secondary"
                            )
                            ui.label(self.user.twitch_name or "Unknown").classes(
                                "font-mono"
                            )

                    # Twitch ID
                    with ui.row().classes("items-center"):
                        ui.icon("fingerprint").classes("text-secondary")
                        with ui.column().classes("flex-1"):
                            ui.label("Twitch ID").classes("text-sm text-secondary")
                            ui.label(self.user.twitch_id).classes("font-mono")

                    ui.separator()

                    # Twitch profile link
                    with ui.row().classes("items-center"):
                        ui.icon("open_in_new").classes("text-secondary")
                        with ui.column().classes("flex-1"):
                            ui.label("Twitch Profile").classes("text-sm text-secondary")
                            ui.link(
                                f"twitch.tv/{self.user.twitch_name}",
                                f"https://www.twitch.tv/{self.user.twitch_name}",
                                new_tab=True,
                            ).classes("text-primary")

                    ui.separator()

                    # Unlink button
                    async def handle_unlink():
                        """Handle unlinking Twitch account."""
                        from components.dialogs.common.tournament_dialogs import (
                            ConfirmDialog,
                        )

                        dialog = ConfirmDialog(
                            title="Unlink Twitch Account",
                            message=(
                                "Are you sure you want to unlink your Twitch "
                                "account? This will remove any Twitch-related "
                                "integrations and features."
                            ),
                            on_confirm=self._unlink_account,
                        )
                        await dialog.show()

                    ui.button("Unlink Account", on_click=handle_unlink).classes(
                        "btn"
                    ).props("color=negative")

                else:
                    # Account is not linked
                    with ui.row().classes("items-center"):
                        ui.icon("link_off").classes("text-warning")
                        with ui.column().classes("flex-1"):
                            ui.label("Account Status").classes("text-sm text-secondary")
                            ui.label("Not Linked").classes("badge badge-warning")

                    ui.separator()

                    # Info about linking
                    with ui.element("div").classes("flex flex-col gap-2"):
                        ui.label("Link your Twitch account to:").classes("text-sm")
                        with ui.element("ul").classes("list-disc pl-6 text-sm"):
                            ui.label(
                                "Enable Twitch-based features and integrations"
                            ).classes("list-item")
                            ui.label(
                                "Connect your streams to tournaments and races"
                            ).classes("list-item")
                            ui.label(
                                "Receive notifications and alerts via Twitch"
                            ).classes("list-item")

                    ui.separator()

                    # Link button
                    ui.button(
                        "Link Twitch Account",
                        on_click=lambda: ui.navigate.to("/twitch/link/initiate"),
                    ).classes("btn btn-primary")

    async def _unlink_account(self) -> None:
        """Unlink the Twitch account via service."""
        from application.services.core.user_service import UserService
        from application.repositories.user_repository import UserRepository

        try:
            # Call the service to unlink the account
            user_service = UserService()
            await user_service.unlink_twitch_account(self.user)

            # Refresh the user object
            user_repo = UserRepository()
            self.user = await user_repo.get_by_id(self.user.id)

            ui.notify("Twitch account unlinked successfully", type="positive")
            # Reload the page to reflect changes
            ui.navigate.to("/profile")

        except Exception as e:
            logger.error("Error unlinking Twitch account: %s", str(e), exc_info=True)
            ui.notify("An error occurred while unlinking your account", type="negative")
