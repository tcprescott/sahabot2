"""
Async Qualifier Pools View.

Shows all pools and their permalinks for a tournament with management UI.
"""

from __future__ import annotations
from nicegui import ui
from models import User
from modules.async_qualifier.models.async_qualifier import AsyncQualifier, AsyncQualifierPool
from components.card import Card
from components.dialogs.async_qualifiers import PoolDialog, PermalinkDialog
from components.dialogs.common import ConfirmDialog
from application.services.async_qualifiers.async_qualifier_service import (
    AsyncQualifierService,
)
import logging

logger = logging.getLogger(__name__)


class AsyncPoolsView:
    """View for async qualifier pools and permalinks with management capabilities."""

    def __init__(self, user: User, tournament: AsyncQualifier):
        self.user = user
        self.tournament = tournament
        self.service = AsyncQualifierService()
        self.can_manage = False
        self.container = None

    async def render(self):
        """Render the pools view."""
        # Check management permissions
        self.can_manage = await self.service.can_manage_async_tournaments(
            self.user, self.tournament.organization_id
        )

        with Card.create(title=f"{self.tournament.name} - Pools"):
            # Add pool button (for admins/mods)
            if self.can_manage:
                ui.button(
                    "Add Pool", icon="add", on_click=lambda: self._show_pool_dialog()
                ).classes("btn-primary mb-3")

            # Container for pools
            self.container = ui.element("div")
            await self._refresh_pools()

    async def _refresh_pools(self):
        """Refresh the pools display."""
        if not self.container:
            return

        self.container.clear()

        with self.container:
            # Get pools with permalinks
            await self.tournament.fetch_related("pools", "pools__permalinks")

            if not self.tournament.pools:
                with ui.element("div").classes("text-center mt-4"):
                    ui.icon("folder_open").classes("text-secondary icon-large")
                    ui.label("No pools configured yet").classes("text-secondary")
                return

            # Render each pool
            for pool in self.tournament.pools:
                await self._render_pool(pool)

    async def _render_pool(self, pool: AsyncQualifierPool):
        """Render a single pool section with management controls."""
        with ui.element("div").classes("card mb-4"):
            # Pool header
            with ui.element("div").classes(
                "card-header flex justify-between items-center"
            ):
                with ui.element("div"):
                    ui.element("h5").classes("mb-1").add_slot("default", pool.name)
                    if pool.description:
                        ui.label(pool.description).classes("text-sm text-secondary")

                # Pool management buttons
                if self.can_manage:
                    with ui.element("div").classes("flex gap-2"):
                        ui.button(
                            icon="add",
                            on_click=lambda p=pool: self._show_permalink_dialog(p),
                        ).classes("btn-sm").props("flat").tooltip("Add Permalink")
                        ui.button(
                            icon="edit",
                            on_click=lambda p=pool: self._show_pool_dialog(p),
                        ).classes("btn-sm").props("flat").tooltip("Edit Pool")
                        ui.button(
                            icon="delete",
                            on_click=lambda p=pool: self._confirm_delete_pool(p),
                        ).classes("btn-sm text-danger").props("flat").tooltip(
                            "Delete Pool"
                        )

            # Pool permalinks
            with ui.element("div").classes("card-body"):
                if not pool.permalinks:
                    ui.label("No permalinks yet").classes("text-secondary")
                else:
                    with ui.element("div").classes("flex flex-col gap-2"):
                        for permalink in pool.permalinks:
                            await self._render_permalink(pool, permalink)

    async def _render_permalink(self, pool: AsyncQualifierPool, permalink):
        """Render a single permalink with management controls."""
        with ui.element("div").classes(
            "flex justify-between items-center p-2 hover-bg"
        ):
            with ui.element("div").classes("flex-grow"):
                # Link to permalink details page
                permalink_link = f"/org/{self.tournament.organization_id}/async/{self.tournament.id}/permalink/{permalink.id}"
                ui.link(permalink.url, permalink_link, new_tab=True)

                # Show par time and notes (hide par time if results are hidden and tournament is active)
                with ui.element("div").classes("text-sm text-secondary"):
                    if permalink.par_time is not None:
                        if not (
                            self.tournament.hide_results and self.tournament.is_active
                        ):
                            ui.label(f"Par: {permalink.par_time_formatted}")
                        else:
                            ui.label("Par: Hidden")
                    if permalink.notes:
                        ui.label(f" - {permalink.notes}")

            # Permalink management buttons
            if self.can_manage:
                with ui.element("div").classes("flex gap-1"):
                    ui.button(
                        icon="edit",
                        on_click=lambda p=permalink: self._show_permalink_dialog(
                            pool, p
                        ),
                    ).classes("btn-sm").props("flat").tooltip("Edit Permalink")
                    ui.button(
                        icon="delete",
                        on_click=lambda p=permalink: self._confirm_delete_permalink(p),
                    ).classes("btn-sm text-danger").props("flat").tooltip(
                        "Delete Permalink"
                    )

    async def _show_pool_dialog(self, pool: AsyncQualifierPool = None):
        """Show dialog for creating/editing a pool."""

        async def on_save(data):
            if pool:
                # Update existing pool
                await self.service.update_pool(
                    self.user, self.tournament.organization_id, pool.id, **data
                )
            else:
                # Create new pool
                await self.service.create_pool(
                    self.user,
                    self.tournament.organization_id,
                    self.tournament.id,
                    **data,
                )
            await self._refresh_pools()

        dialog = PoolDialog(pool=pool, on_save=on_save)
        await dialog.show()

    async def _show_permalink_dialog(self, pool: AsyncQualifierPool, permalink=None):
        """Show dialog for creating/editing a permalink."""

        async def on_save(data):
            if permalink:
                # Update existing permalink
                await self.service.update_permalink(
                    self.user, self.tournament.organization_id, permalink.id, **data
                )
            else:
                # Create new permalink
                await self.service.create_permalink(
                    self.user, self.tournament.organization_id, pool.id, **data
                )
            await self._refresh_pools()

        dialog = PermalinkDialog(permalink=permalink, on_save=on_save)
        await dialog.show()

    async def _confirm_delete_pool(self, pool: AsyncQualifierPool):
        """Confirm and delete a pool."""

        async def do_delete():
            success = await self.service.delete_pool(
                self.user, self.tournament.organization_id, pool.id
            )
            if success:
                ui.notify("Pool deleted successfully", type="positive")
                await self._refresh_pools()
            else:
                ui.notify("Failed to delete pool", type="negative")

        dialog = ConfirmDialog(
            title=f"Delete Pool: {pool.name}?",
            message="This will delete all permalinks and races in this pool.",
            on_confirm=do_delete,
        )
        await dialog.show()

    async def _confirm_delete_permalink(self, permalink):
        """Confirm and delete a permalink."""

        async def do_delete():
            success = await self.service.delete_permalink(
                self.user, self.tournament.organization_id, permalink.id
            )
            if success:
                ui.notify("Permalink deleted successfully", type="positive")
                await self._refresh_pools()
            else:
                ui.notify("Failed to delete permalink", type="negative")

        dialog = ConfirmDialog(
            title="Delete this permalink?",
            message="This will delete all races for this permalink.",
            on_confirm=do_delete,
        )
        await dialog.show()
