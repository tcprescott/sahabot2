"""Racer verification configuration dialog."""

import logging
from nicegui import ui
from components.dialogs.common.base_dialog import BaseDialog
from application.services.racetime.racer_verification_service import (
    RacerVerificationService,
)
from application.services.discord.discord_guild_service import DiscordGuildService

logger = logging.getLogger(__name__)


class RacerVerificationDialog(BaseDialog):
    """Dialog for creating/editing racer verification configurations."""

    def __init__(self, organization_id: int, verification=None, on_save=None):
        """
        Initialize dialog.

        Args:
            organization_id: Organization ID
            verification: RacerVerification to edit (None for create)
            on_save: Callback after successful save
        """
        super().__init__()
        self.organization_id = organization_id
        self.verification = verification
        self.on_save = on_save
        self.service = RacerVerificationService()
        self.guild_service = DiscordGuildService()

        # Form fields
        self.guild_select = None
        self.role_select = None
        self.category_input = None
        self.minimum_races_input = None
        self.count_forfeits_checkbox = None
        self.count_dq_checkbox = None

        # State
        self.guilds = []
        self.selected_guild_id = None
        self.roles = []

    async def show(self):
        """Display the dialog."""
        title = (
            "Edit Racer Verification"
            if self.verification
            else "Create Racer Verification"
        )
        icon = "edit" if self.verification else "add"

        self.create_dialog(title=title, icon=icon, max_width="700px")

        await super().show()

    def _render_body(self):
        """Render dialog content."""
        # Info section
        self.create_section_title("Configuration")

        with ui.element("div").classes("text-secondary mb-4"):
            ui.label(
                "Configure a Discord role to be automatically granted to users who have "
                "completed a minimum number of races in a specific RaceTime category."
            ).classes("text-sm")

        # Form
        with self.create_form_grid(columns=2):
            # Discord Guild
            with ui.element("div"):
                self.guild_select = ui.select(
                    label="Discord Server", options={}, on_change=self._on_guild_change
                ).classes("w-full")

                # Load guilds asynchronously
                ui.timer(0.1, self._load_guilds, once=True)

            # Discord Role
            with ui.element("div"):
                self.role_select = ui.select(
                    label="Discord Role",
                    options={},
                ).classes("w-full")

                if self.verification:
                    self.role_select.set_value(self.verification.role_id)

            # RaceTime Categories
            with ui.element("div"):
                self.categories_input = ui.input(
                    label="RaceTime Categories (comma-separated)",
                    value=(
                        ", ".join(self.verification.categories)
                        if self.verification and self.verification.categories
                        else ""
                    ),
                    placeholder="e.g., alttpr, alttprbiweekly",
                ).classes("w-full")
                ui.label(
                    "Category slugs from racetime.gg URLs, separated by commas"
                ).classes("text-xs text-secondary")

            # Minimum Races
            with ui.element("div"):
                self.minimum_races_input = ui.number(
                    label="Minimum Races",
                    value=self.verification.minimum_races if self.verification else 5,
                    min=1,
                    max=1000,
                    precision=0,
                ).classes("w-full")

        # Counting Rules
        ui.separator()
        self.create_section_title("Counting Rules")

        with ui.column().classes("gap-2"):
            self.count_forfeits_checkbox = ui.checkbox(
                "Count Forfeits (DNF)",
                value=self.verification.count_forfeits if self.verification else False,
            )
            ui.label("Include forfeited races in the count").classes(
                "text-sm text-secondary ml-8"
            )

            self.count_dq_checkbox = ui.checkbox(
                "Count Disqualifications",
                value=self.verification.count_dq if self.verification else False,
            )
            ui.label("Include disqualified races in the count").classes(
                "text-sm text-secondary ml-8"
            )

        ui.separator()

        # Actions
        with self.create_actions_row():
            ui.button("Cancel", on_click=self.close).classes("btn")
            ui.button("Save", on_click=self._save).classes("btn").props(
                "color=positive"
            )

    async def _load_guilds(self):
        """Load Discord guilds for organization."""
        from discordbot.client import get_bot_instance
        from middleware.auth import DiscordAuthService

        bot = get_bot_instance()
        if not bot:
            ui.notify("Discord bot not available", type="warning")
            return

        # Get current user
        current_user = await DiscordAuthService.get_current_user()

        # Get guilds linked to organization
        guilds = await self.guild_service.list_guilds(
            current_user, self.organization_id
        )

        # Build options
        options = {}
        for guild in guilds:
            discord_guild = bot.get_guild(guild.guild_id)
            if discord_guild:
                options[guild.guild_id] = discord_guild.name
                self.guilds.append(
                    {
                        "id": guild.guild_id,
                        "name": discord_guild.name,
                        "discord_guild": discord_guild,
                    }
                )

        self.guild_select.set_options(options)

        # Set initial value
        if self.verification:
            self.guild_select.set_value(self.verification.guild_id)
            self.selected_guild_id = self.verification.guild_id
            await self._load_roles()

    async def _on_guild_change(self, e):
        """Handle guild selection change."""
        self.selected_guild_id = e.value
        await self._load_roles()

    async def _load_roles(self):
        """Load roles for selected guild."""
        if not self.selected_guild_id:
            return

        # Find guild
        guild_data = next(
            (g for g in self.guilds if g["id"] == self.selected_guild_id), None
        )

        if not guild_data:
            return

        discord_guild = guild_data["discord_guild"]

        # Get bot member to check role permissions
        bot_member = discord_guild.get_member(discord_guild.me.id)

        # Build role options (exclude @everyone and roles bot can't manage)
        options = {}
        for role in discord_guild.roles:
            if role.name == "@everyone":
                continue

            # Check if bot can manage this role
            # Bot must have manage_roles permission AND role must be below bot's highest role
            can_manage = False
            if bot_member and bot_member.guild_permissions.manage_roles:
                # Check role hierarchy - bot can only manage roles below its highest role
                bot_top_role = bot_member.top_role
                can_manage = role < bot_top_role

            # Add role with permission indicator
            if can_manage:
                options[role.id] = role.name
            else:
                options[role.id] = f"{role.name} ⚠️ (Bot cannot manage)"

        self.role_select.set_options(options)

        # Set initial value for edit mode
        if self.verification and self.verification.guild_id == self.selected_guild_id:
            self.role_select.set_value(self.verification.role_id)

    async def _save(self):
        """Save verification."""
        # Validation
        if not self.selected_guild_id:
            ui.notify("Please select a Discord server", type="negative")
            return

        if not self.role_select.value:
            ui.notify("Please select a Discord role", type="negative")
            return

        if not self.categories_input.value:
            ui.notify("Please enter at least one RaceTime category", type="negative")
            return

        if not self.minimum_races_input.value or self.minimum_races_input.value < 1:
            ui.notify("Minimum races must be at least 1", type="negative")
            return

        # Parse categories (comma-separated, trim whitespace)
        categories = [
            cat.strip() for cat in self.categories_input.value.split(",") if cat.strip()
        ]

        if not categories:
            ui.notify(
                "Please enter at least one valid RaceTime category", type="negative"
            )
            return

        # Get role name
        guild_data = next(
            (g for g in self.guilds if g["id"] == self.selected_guild_id), None
        )
        role_name = "Unknown Role"
        bot_can_manage = False
        if guild_data:
            discord_guild = guild_data["discord_guild"]
            role = next(
                (r for r in discord_guild.roles if r.id == self.role_select.value), None
            )
            if role:
                role_name = role.name

                # Check if bot can manage this role
                bot_member = discord_guild.get_member(discord_guild.me.id)
                if bot_member and bot_member.guild_permissions.manage_roles:
                    bot_top_role = bot_member.top_role
                    bot_can_manage = role < bot_top_role

        # Warn if bot cannot manage the role
        if not bot_can_manage:
            ui.notify(
                f'Warning: Bot cannot manage role "{role_name}". Verification will be created but role assignment will fail.',
                type="warning",
                timeout=10000,
            )

        # Get current user
        from middleware.auth import DiscordAuthService

        current_user = await DiscordAuthService.get_current_user()

        try:
            if self.verification:
                # Update
                await self.service.update_verification(
                    current_user=current_user,
                    verification_id=self.verification.id,
                    guild_id=self.selected_guild_id,
                    role_id=self.role_select.value,
                    role_name=role_name,
                    categories=categories,
                    minimum_races=int(self.minimum_races_input.value),
                    count_forfeits=self.count_forfeits_checkbox.value,
                    count_dq=self.count_dq_checkbox.value,
                )
                ui.notify("Racer verification updated", type="positive")
            else:
                # Create
                await self.service.create_verification(
                    current_user=current_user,
                    organization_id=self.organization_id,
                    guild_id=self.selected_guild_id,
                    role_id=self.role_select.value,
                    role_name=role_name,
                    categories=categories,
                    minimum_races=int(self.minimum_races_input.value),
                    count_forfeits=self.count_forfeits_checkbox.value,
                    count_dq=self.count_dq_checkbox.value,
                )
                ui.notify("Racer verification created", type="positive")

            # Callback
            if self.on_save:
                await self.on_save()

            await self.close()

        except Exception as e:
            logger.error("Error saving racer verification: %s", e, exc_info=True)
            ui.notify(f"Error: {str(e)}", type="negative")
