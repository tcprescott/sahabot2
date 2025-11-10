"""
Organization Async Tournaments view.

List, create, edit, and delete async tournaments within an organization.
"""

from __future__ import annotations
from typing import Any
from nicegui import ui
from models import Organization
from models.async_tournament import AsyncTournament
from models.discord_guild import DiscordGuild
from components.card import Card
from components.data_table import ResponsiveTable, TableColumn
from components.dialogs import AsyncTournamentDialog, ConfirmDialog
from application.services.tournaments.async_tournament_service import (
    AsyncTournamentService,
)
from discordbot.client import get_bot_instance
import logging

logger = logging.getLogger(__name__)


class OrganizationAsyncTournamentsView:
    """Manage async tournaments for an organization."""

    def __init__(self, organization: Organization, user: Any) -> None:
        self.organization = organization
        self.user = user
        self.service = AsyncTournamentService()
        self.container = None

    async def _refresh(self) -> None:
        """Re-render the async tournaments list."""
        if self.container:
            self.container.clear()
            with self.container:
                await self._render_content()

    async def _get_discord_channels(self) -> list[tuple[int, str]]:
        """Get available Discord text channels from linked guilds."""
        channels = []

        # Get the Discord bot instance
        bot = get_bot_instance()
        if not bot or not bot.is_ready:
            logger.warning("Discord bot not available for fetching channels")
            return channels

        # Get linked Discord guilds for this organization
        guilds = await DiscordGuild.filter(
            organization_id=self.organization.id, is_active=True
        ).all()

        for guild in guilds:
            try:
                # Fetch the Discord guild from Discord API (not cache)
                discord_guild = await bot.fetch_guild(guild.guild_id)
                if not discord_guild:
                    logger.warning("Discord guild %s not found", guild.guild_id)
                    continue

                # Fetch all channels for the guild
                guild_channels = await discord_guild.fetch_channels()

                # Filter for text channels the bot can view
                for channel in guild_channels:
                    # Check if it's a text channel (type 0) or thread
                    if (
                        hasattr(channel, "type") and channel.type.value == 0
                    ):  # Text channel
                        # Check if bot has view permissions
                        try:
                            permissions = channel.permissions_for(discord_guild.me)
                            if permissions.view_channel:
                                channels.append(
                                    (channel.id, f"{guild.guild_name}: #{channel.name}")
                                )
                        except Exception as e:
                            logger.debug(
                                "Could not check permissions for channel %s: %s",
                                channel.id,
                                e,
                            )
                            # Add anyway if we can't check permissions
                            channels.append(
                                (channel.id, f"{guild.guild_name}: #{channel.name}")
                            )

            except Exception as e:
                logger.error(
                    "Error fetching channels from guild %s: %s", guild.guild_id, e
                )
                continue

        return channels

    async def _open_create_dialog(self) -> None:
        """Open dialog to create a new async tournament."""
        # Get available Discord channels
        discord_channels = await self._get_discord_channels()

        async def on_save(data: dict) -> None:
            tournament, warnings = await self.service.create_tournament(
                user=self.user,
                organization_id=self.organization.id,
                name=data["name"],
                description=data.get("description"),
                is_active=data.get("is_active", True),
                hide_results=data.get("hide_results", False),
                discord_channel_id=data.get("discord_channel_id"),
                runs_per_pool=data.get("runs_per_pool", 1),
                require_racetime_for_async_runs=data.get(
                    "require_racetime_for_async_runs", False
                ),
            )
            if tournament:
                ui.notify("Async tournament created successfully", type="positive")

                # Display warnings if any
                if warnings:
                    for warning in warnings:
                        ui.notify(f"Warning: {warning}", type="warning")

                await self._refresh()
            else:
                ui.notify("Failed to create async tournament", type="negative")

        dialog = AsyncTournamentDialog(
            tournament=None, on_save=on_save, discord_channels=discord_channels
        )
        await dialog.show()

    async def _open_edit_dialog(self, tournament: AsyncTournament) -> None:
        """Open dialog to edit an existing async tournament."""
        # Get available Discord channels
        discord_channels = await self._get_discord_channels()

        async def on_save(data: dict) -> None:
            updated, warnings = await self.service.update_tournament(
                user=self.user,
                organization_id=self.organization.id,
                tournament_id=tournament.id,
                **data,
            )
            if updated:
                ui.notify("Async tournament updated successfully", type="positive")

                # Display warnings if any
                if warnings:
                    for warning in warnings:
                        ui.notify(f"Warning: {warning}", type="warning")

                await self._refresh()
            else:
                ui.notify("Failed to update async tournament", type="negative")

        dialog = AsyncTournamentDialog(
            tournament=tournament, on_save=on_save, discord_channels=discord_channels
        )
        await dialog.show()

    async def _confirm_delete(self, tournament: AsyncTournament) -> None:
        """Ask for confirmation and delete the async tournament if confirmed."""

        async def do_delete() -> None:
            success = await self.service.delete_tournament(
                user=self.user,
                organization_id=self.organization.id,
                tournament_id=tournament.id,
            )
            if success:
                ui.notify("Async tournament deleted successfully", type="positive")
                await self._refresh()
            else:
                ui.notify("Failed to delete async tournament", type="negative")

        dialog = ConfirmDialog(
            title="Delete Async Tournament",
            message=f"Are you sure you want to delete '{tournament.name}'? This will also delete all pools, permalinks, and race data.",
            on_confirm=do_delete,
        )
        await dialog.show()

    async def _check_channel_permissions(
        self, tournament: AsyncTournament, force_recheck: bool = False
    ) -> list[str]:
        """
        Check permissions for a tournament's Discord channel.

        Uses cached warnings unless force_recheck is True or cache is stale.

        Args:
            tournament: The tournament to check permissions for
            force_recheck: If True, bypass cache and check Discord API

        Returns:
            List of warning strings
        """
        if not tournament.discord_channel_id:
            return []

        # Use cached warnings if available and not forcing recheck
        if not force_recheck and tournament.discord_warnings is not None:
            logger.debug(
                "Using cached permissions for tournament %s (checked at %s)",
                tournament.id,
                tournament.discord_warnings_checked_at,
            )
            return tournament.discord_warnings

        # Check permissions via Discord API
        try:
            from application.services.discord.discord_guild_service import (
                DiscordGuildService,
            )
            from datetime import datetime, timezone

            discord_service = DiscordGuildService()
            perm_check = (
                await discord_service.check_async_tournament_channel_permissions(
                    tournament.discord_channel_id
                )
            )

            # Update cache
            tournament.discord_warnings = perm_check.warnings
            tournament.discord_warnings_checked_at = datetime.now(timezone.utc)
            await tournament.save(
                update_fields=["discord_warnings", "discord_warnings_checked_at"]
            )

            logger.info(
                "Checked permissions for tournament %s: %d warnings",
                tournament.id,
                len(perm_check.warnings),
            )

            return perm_check.warnings

        except Exception as e:
            logger.error(
                "Error checking channel permissions for tournament %s: %s",
                tournament.id,
                e,
            )
            return ["Could not verify channel permissions"]

    async def _post_embed_to_discord(self, tournament: AsyncTournament) -> None:
        """Post the tournament embed to the configured Discord channel."""
        if not tournament.discord_channel_id:
            ui.notify(
                "No Discord channel configured for this tournament", type="warning"
            )
            return

        # Get the Discord bot instance
        bot = get_bot_instance()
        if not bot or not bot.is_ready:
            ui.notify("Discord bot is not available", type="negative")
            return

        try:
            # Get the channel
            channel = await bot.fetch_channel(tournament.discord_channel_id)
            if not channel:
                ui.notify("Discord channel not found", type="negative")
                return

            # Try to check permissions if available (without requiring members intent)
            # We'll attempt to send and let Discord reject if we don't have permission
            can_send = True
            if hasattr(channel, "permissions_for") and hasattr(channel, "guild"):
                try:
                    # Try to get bot member, but don't fail if we can't
                    bot_member = channel.guild.get_member(bot.user.id)
                    if bot_member:
                        permissions = channel.permissions_for(bot_member)
                        can_send = permissions.send_messages
                        if not can_send:
                            ui.notify(
                                "Bot does not have permission to send messages in this channel",
                                type="negative",
                            )
                            return
                except Exception as perm_error:
                    # Can't check permissions without members intent, will try sending anyway
                    logger.debug(
                        "Could not check permissions (expected without members intent): %s",
                        perm_error,
                    )

            # Import Discord embed
            import discord
            from discordbot.async_tournament_views import AsyncTournamentMainView

            # Create the embed
            embed = discord.Embed(
                title=tournament.name,
                description=tournament.description or "Async Tournament",
                color=discord.Color.blue(),
            )
            embed.add_field(
                name="How to Participate",
                value="Click 'Start New Async Run' below to begin a new race.",
                inline=False,
            )
            embed.add_field(
                name="Status",
                value="Active" if tournament.is_active else "Inactive",
                inline=True,
            )
            embed.add_field(
                name="Runs Per Pool", value=str(tournament.runs_per_pool), inline=True
            )
            embed.set_footer(text=f"Tournament ID: {tournament.id}")

            # Send the message with the persistent view
            await channel.send(embed=embed, view=AsyncTournamentMainView())

            ui.notify(
                "Tournament embed posted to Discord successfully!", type="positive"
            )
            logger.info(
                "Posted async tournament embed for tournament %s to channel %s",
                tournament.id,
                tournament.discord_channel_id,
            )

        except Exception as e:
            logger.error(
                "Error posting embed to Discord for tournament %s: %s",
                tournament.id,
                e,
                exc_info=True,
            )
            ui.notify(f"Failed to post embed to Discord: {str(e)}", type="negative")

    async def _render_content(self) -> None:
        """Render async tournaments list and actions."""
        tournaments = await self.service.list_org_tournaments(
            self.user, self.organization.id
        )

        # Use cached permissions - avoid API calls on page load
        tournament_warnings = {}
        for tournament in tournaments:
            if tournament.discord_channel_id:
                # Use cached warnings (pass force_recheck=False)
                warnings = await self._check_channel_permissions(
                    tournament, force_recheck=False
                )
                if warnings:
                    tournament_warnings[tournament.id] = warnings

        async def recheck_permissions(tournament: AsyncTournament) -> None:
            """Force recheck of Discord permissions for a tournament."""
            ui.notify("Checking Discord permissions...", type="info")
            warnings = await self._check_channel_permissions(
                tournament, force_recheck=True
            )

            if warnings:
                ui.notify(f"Found {len(warnings)} permission issue(s)", type="warning")
            else:
                ui.notify("All permissions OK", type="positive")

            # Refresh the view to show updated warnings
            await self._refresh()

        with Card.create(title="Async Tournaments"):
            with ui.row().classes("w-full justify-between mb-2"):
                ui.label(f"{len(tournaments)} async tournament(s) in this organization")
                ui.button(
                    "New Async Tournament",
                    icon="add",
                    on_click=self._open_create_dialog,
                ).props("color=positive").classes("btn")

            if not tournaments:
                with ui.element("div").classes("text-center mt-4"):
                    ui.icon("emoji_events").classes("text-secondary icon-large")
                    ui.label("No async tournaments yet").classes("text-secondary")
                    ui.label('Click "New Async Tournament" to create one').classes(
                        "text-secondary text-sm"
                    )
            else:

                def render_active(t: AsyncTournament):
                    if t.is_active:
                        with ui.row().classes("items-center gap-sm"):
                            ui.icon("check_circle").classes("text-positive")
                            ui.label("Active")
                    else:
                        with ui.row().classes("items-center gap-sm"):
                            ui.icon("cancel").classes("text-negative")
                            ui.label("Inactive")

                def render_discord_channel(t: AsyncTournament):
                    if t.discord_channel_id:
                        with ui.row().classes("items-center gap-sm"):
                            ui.icon("discord").classes("text-info")
                            ui.label(f"Channel ID: {t.discord_channel_id}")
                    else:
                        ui.label("-").classes("text-secondary")

                def render_permissions_warnings(t: AsyncTournament):
                    warnings = tournament_warnings.get(t.id, [])
                    with ui.column().classes("gap-1"):
                        if warnings:
                            for warning in warnings:
                                with ui.row().classes("items-center gap-1"):
                                    ui.icon("warning").classes("text-warning text-sm")
                                    ui.label(warning).classes("text-warning text-xs")
                        else:
                            if t.discord_channel_id:
                                with ui.row().classes("items-center gap-sm"):
                                    ui.icon("check_circle").classes(
                                        "text-positive text-sm"
                                    )
                                    ui.label("OK").classes("text-positive text-xs")
                            else:
                                ui.label("-").classes("text-secondary")

                        # Add recheck button for tournaments with Discord channels
                        if t.discord_channel_id:
                            from datetime import datetime, timezone

                            checked_text = ""
                            if t.discord_warnings_checked_at:
                                # Format as relative time
                                delta = (
                                    datetime.now(timezone.utc)
                                    - t.discord_warnings_checked_at
                                )
                                if delta.days > 0:
                                    checked_text = f"(checked {delta.days}d ago)"
                                elif delta.seconds > 3600:
                                    checked_text = (
                                        f"(checked {delta.seconds // 3600}h ago)"
                                    )
                                else:
                                    checked_text = (
                                        f"(checked {delta.seconds // 60}m ago)"
                                    )

                            with ui.row().classes("items-center gap-1 mt-1"):
                                ui.button(
                                    "Recheck",
                                    icon="refresh",
                                    on_click=lambda t=t: recheck_permissions(t),
                                ).props("size=xs flat dense").classes("text-xs")
                                if checked_text:
                                    ui.label(checked_text).classes(
                                        "text-secondary text-xs"
                                    )

                def render_runs_per_pool(t: AsyncTournament):
                    ui.label(str(t.runs_per_pool))

                def render_actions(t: AsyncTournament):
                    with ui.element("div").classes("flex gap-2"):
                        # Post Embed button (only show if Discord channel is configured)
                        if t.discord_channel_id:
                            ui.button(
                                "Post Embed",
                                icon="send",
                                on_click=lambda t=t: self._post_embed_to_discord(t),
                            ).props("color=info").classes("btn")

                        ui.button(
                            "Admin",
                            icon="admin_panel_settings",
                            on_click=lambda t=t: ui.navigate.to(
                                f"/org/{self.organization.id}/async/{t.id}/admin"
                            ),
                        ).classes("btn btn-primary")
                        ui.button(
                            "Manage",
                            icon="settings",
                            on_click=lambda t=t: ui.navigate.to(
                                f"/org/{self.organization.id}/async/{t.id}/pools"
                            ),
                        ).classes("btn")
                        ui.button(
                            "Edit",
                            icon="edit",
                            on_click=lambda t=t: self._open_edit_dialog(t),
                        ).classes("btn")
                        ui.button(
                            "Delete",
                            icon="delete",
                            on_click=lambda t=t: self._confirm_delete(t),
                        ).classes("btn btn-danger")

                columns = [
                    TableColumn("Name", key="name"),
                    TableColumn(
                        "Description",
                        cell_render=lambda t: ui.label(
                            str(t.description or "")
                        ).classes("truncate max-w-64"),
                    ),
                    TableColumn("Status", cell_render=render_active),
                    TableColumn("Runs/Pool", cell_render=render_runs_per_pool),
                    TableColumn("Discord Channel", cell_render=render_discord_channel),
                    TableColumn("Permissions", cell_render=render_permissions_warnings),
                    TableColumn("Actions", cell_render=render_actions),
                ]
                table = ResponsiveTable(columns, tournaments)
                await table.render()

    async def render(self) -> None:
        """Render the async tournaments view."""
        self.container = ui.column().classes("full-width")
        with self.container:
            await self._render_content()
