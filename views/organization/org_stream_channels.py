"""
Organization Stream Channels view.

List, create, edit, and delete stream channels within an organization.
"""

from __future__ import annotations
from typing import Any, Optional
from nicegui import ui
from models import Organization
from components.card import Card
from components.data_table import ResponsiveTable, TableColumn
from components.datetime_label import DateTimeLabel
from components.dialogs import StreamChannelDialog, ConfirmDialog
from modules.tournament.services.stream_channel_service import StreamChannelService


class OrganizationStreamChannelsView:
    """Manage stream channels for an organization."""

    def __init__(self, organization: Organization, user: Any) -> None:
        self.organization = organization
        self.user = user
        self.service = StreamChannelService()
        self.container = None

    async def _refresh(self) -> None:
        """Re-render the stream channels list."""
        if self.container:
            self.container.clear()
            with self.container:
                await self._render_content()

    async def _open_create_dialog(self) -> None:
        """Open dialog to create a new stream channel."""

        async def on_submit(
            name: str, stream_url: Optional[str], is_active: bool
        ) -> None:
            await self.service.create_channel(
                self.user, self.organization.id, name, stream_url, is_active
            )
            await self._refresh()

        dialog = StreamChannelDialog(
            title="New Stream Channel",
            on_submit=on_submit,
            initial_is_active=True,
        )
        await dialog.show()

    async def _open_edit_dialog(self, channel) -> None:
        """Open dialog to edit an existing stream channel."""

        async def on_submit(
            name: str, stream_url: Optional[str], is_active: bool
        ) -> None:
            await self.service.update_channel(
                self.user,
                self.organization.id,
                channel.id,
                name=name,
                stream_url=stream_url,
                is_active=is_active,
            )
            await self._refresh()

        dialog = StreamChannelDialog(
            title=f'Edit {getattr(channel, "name", "Stream Channel")}',
            initial_name=getattr(channel, "name", ""),
            initial_stream_url=getattr(channel, "stream_url", None),
            initial_is_active=bool(getattr(channel, "is_active", True)),
            on_submit=on_submit,
        )
        await dialog.show()

    async def _confirm_delete(self, channel) -> None:
        """Ask for confirmation and delete the stream channel if confirmed."""

        async def do_delete() -> None:
            await self.service.delete_channel(
                self.user, self.organization.id, channel.id
            )
            await self._refresh()

        dialog = ConfirmDialog(
            title="Delete Stream Channel",
            message=f"Are you sure you want to delete '{getattr(channel, 'name', 'Stream Channel')}'?",
            on_confirm=do_delete,
        )
        await dialog.show()

    async def _render_content(self) -> None:
        """Render stream channels list and actions."""
        channels = await self.service.list_org_channels(self.user, self.organization.id)

        with Card.create(title="Stream Channels"):
            with ui.row().classes("w-full justify-between mb-2"):
                ui.label(f"{len(channels)} stream channel(s) in this organization")
                ui.button(
                    "New Channel", icon="add", on_click=self._open_create_dialog
                ).props("color=positive").classes("btn")

            if not channels:
                with ui.element("div").classes("text-center mt-4"):
                    ui.icon("cast").classes("text-secondary icon-large")
                    ui.label("No stream channels yet").classes("text-secondary")
                    ui.label('Click "New Channel" to create one').classes(
                        "text-secondary text-sm"
                    )
            else:

                def render_url(c):
                    url = getattr(c, "stream_url", None)
                    if url:
                        with ui.link(target=url, new_tab=True):
                            ui.label(str(url)).classes("truncate max-w-64 text-primary")
                    else:
                        ui.label("—").classes("text-secondary")

                def render_active(c):
                    if getattr(c, "is_active", False):
                        with ui.row().classes("items-center gap-sm"):
                            ui.icon("check_circle").classes("text-positive")
                            ui.label("Active")
                    else:
                        with ui.row().classes("items-center gap-sm"):
                            ui.icon("cancel").classes("text-negative")
                            ui.label("Inactive")

                def render_created(c):
                    created_at = getattr(c, "created_at", None)
                    if created_at:
                        DateTimeLabel.create(created_at, format_type="relative")
                    else:
                        ui.label("—").classes("text-secondary")

                def render_actions(c):
                    with ui.element("div").classes("flex gap-2"):
                        ui.button(
                            "Edit",
                            icon="edit",
                            on_click=lambda c=c: self._open_edit_dialog(c),
                        ).classes("btn")
                        ui.button(
                            "Delete",
                            icon="delete",
                            on_click=lambda c=c: self._confirm_delete(c),
                        ).classes("btn").props("color=negative")

                columns = [
                    TableColumn("Name", key="name"),
                    TableColumn("Stream URL", cell_render=render_url),
                    TableColumn("Status", cell_render=render_active),
                    TableColumn("Created", cell_render=render_created),
                    TableColumn("Actions", cell_render=render_actions),
                ]
                table = ResponsiveTable(columns, channels)
                await table.render()

    async def render(self) -> None:
        """Render the stream channels view."""
        self.container = ui.column().classes("full-width")
        with self.container:
            await self._render_content()
