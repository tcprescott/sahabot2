"""
Match action handlers for tournament schedules.

Handles actions like generating seeds, creating RaceTime rooms, and managing match status.
"""

from __future__ import annotations
import logging
from datetime import datetime, timezone, timedelta
from typing import TYPE_CHECKING, Callable, Awaitable, Optional
from nicegui import ui
from models import Match
from components.dialogs import MatchSeedDialog, EditMatchDialog
from application.services.randomizer.randomizer_service import RandomizerService
from config import Settings

if TYPE_CHECKING:
    from models import User, Organization
    from application.services.tournaments import TournamentService

settings = Settings()
logger = logging.getLogger(__name__)


class MatchActions:
    """Match action handlers for tournament schedules."""

    def __init__(
        self,
        user: User,
        organization: Organization,
        service: "TournamentService",
        can_manage_tournaments: bool,
        on_refresh: Callable[[], Awaitable[None]],
    ):
        """Initialize match actions.

        Args:
            user: Current user
            organization: Current organization
            service: Tournament service instance
            can_manage_tournaments: Whether user can manage tournaments
            on_refresh: Callback to refresh the view
        """
        self.user = user
        self.organization = organization
        self.service = service
        self.can_manage_tournaments = can_manage_tournaments
        self.on_refresh = on_refresh

    async def generate_seed(
        self, 
        match_id: int, 
        match_title: str, 
        randomizer_type: str,
        randomizer_preset_id: Optional[int],
        button: Optional[ui.button] = None
    ) -> None:
        """Generate a seed using tournament's randomizer settings.

        Args:
            match_id: Match ID
            match_title: Match title for error messages
            randomizer_type: Type of randomizer (alttpr, smz3, etc.)
            randomizer_preset_id: ID of randomizer preset to use (if any)
            button: Button reference for spinner state (optional)
        """
        # Show spinner on button if provided
        if button:
            button.props("loading")
            button.disable()

        try:
            randomizer_service = RandomizerService()

            # Get the randomizer
            randomizer = randomizer_service.get_randomizer(randomizer_type)

            # Prepare settings
            settings_dict = {}
            description = f"Generated {randomizer_type} seed"

            # Generate seed (use preset if configured)
            if randomizer_preset_id:
                # Import here to avoid circular dependency
                from application.repositories.randomizer_preset_repository import RandomizerPresetRepository
                preset_repo = RandomizerPresetRepository()
                preset = await preset_repo.get_by_id(randomizer_preset_id)
                if preset:
                    # Extract settings from preset
                    settings_dict = preset.settings.get(
                        "settings", preset.settings
                    )
                    description = f"Generated {randomizer_type} seed using preset: {preset.name}"
                else:
                    # Preset not found, log warning but continue with defaults
                    logger.warning(
                        "Preset %s not found",
                        randomizer_preset_id,
                    )

            # Generate the seed with settings
            result = await randomizer.generate(settings_dict)

            # Set the seed for the match
            await self.service.set_match_seed(
                self.user,
                self.organization.id,
                match_id,
                result.url,
                description,
            )
            ui.notify("Seed generated successfully", type="positive")
            await self.on_refresh()

        except ValueError as e:
            logger.error("Failed to generate seed: %s", e)
            ui.notify(f"Failed to generate seed: {str(e)}", type="negative")
        except Exception as e:
            logger.error("Failed to generate seed: %s", e)
            ui.notify(f"Error generating seed: {str(e)}", type="negative")
        finally:
            # Remove spinner from button if provided
            if button:
                button.props(remove="loading")
                button.enable()

    async def open_seed_dialog(self, match: Match) -> None:
        """Open dialog to set/edit seed for a match.
        
        Args:
            match: Match object with seed information
        """

        seed = getattr(match, "seed", None)
        if seed and hasattr(seed, "__iter__") and not isinstance(seed, str):
            seed_list = list(seed) if not isinstance(seed, list) else seed
            seed = seed_list[0] if seed_list else None

        initial_url = seed.url if seed else ""
        initial_description = seed.description if seed else None

        async def on_submit(url: str, description: Optional[str]):
            await self.service.set_match_seed(
                self.user, self.organization.id, match.id, url, description
            )
            ui.notify("Seed updated", type="positive")
            await self.on_refresh()

        async def on_delete():
            await self.service.delete_match_seed(
                self.user, self.organization.id, match.id
            )
            ui.notify("Seed deleted", type="positive")
            await self.on_refresh()

        dialog = MatchSeedDialog(
            match_title=match.title or f"Match #{match.id}",
            initial_url=initial_url,
            initial_description=initial_description,
            on_submit=on_submit,
            on_delete=on_delete if seed else None,
        )
        await dialog.show()

    def render_seed(self, match: Match) -> None:
        """Render seed/ROM link if available with action buttons.
        
        Args:
            match: Match object to render seed for
        """
        # Check if seed exists (1:1 relationship)
        seed = getattr(match, "seed", None)

        # Handle the case where seed is a ReverseRelation (list)
        if seed and hasattr(seed, "__iter__") and not isinstance(seed, str):
            seed_list = list(seed) if not isinstance(seed, list) else seed
            seed = seed_list[0] if seed_list else None

        with ui.column().classes("gap-2"):
            if seed:
                # Show link to seed URL
                with ui.link(target=seed.url, new_tab=True).classes(
                    "text-primary"
                ):
                    with ui.row().classes("items-center gap-1"):
                        ui.icon("file_download").classes("text-sm")
                        ui.label("Seed")
                # Show description if available
                if seed.description:
                    ui.label(seed.description).classes(
                        "text-secondary text-xs"
                    )
            else:
                ui.label("—").classes("text-secondary")

            # Add buttons for tournament managers
            if self.can_manage_tournaments:
                with ui.row().classes("gap-1"):
                    # Generate Seed button (with dice icon) - only if tournament has randomizer configured
                    if match.tournament.randomizer:
                        # Create button reference first
                        button = ui.button(
                            icon="casino",
                        ).classes("btn btn-sm").props(
                            "flat color=positive size=sm"
                        ).tooltip(
                            "Generate seed using tournament randomizer"
                        )
                        
                        # Create async handler that captures match data and button
                        async def handle_generate_seed(
                            m_id=match.id, 
                            m_title=match.title,
                            rand_type=match.tournament.randomizer,
                            preset_id=match.tournament.randomizer_preset_id,
                            btn=button
                        ):
                            await self.generate_seed(m_id, m_title, rand_type, preset_id, btn)
                        
                        # Assign the async handler
                        button.on_click(handle_generate_seed)

                    # Set/Edit Seed button (manual URL entry)
                    icon = "edit" if seed else "add"
                    tooltip = (
                        "Edit seed" if seed else "Set seed URL manually"
                    )
                    ui.button(
                        icon=icon,
                        on_click=lambda m=match: self.open_seed_dialog(m),
                    ).classes("btn btn-sm").props(
                        "flat color=primary size=sm"
                    ).tooltip(
                        tooltip
                    )

    async def create_racetime_room(self, match_id: int, button: Optional[ui.button] = None) -> None:
        """Create a RaceTime room for a match (moderator action).

        Args:
            match_id: Match ID
            button: Button reference for spinner state (optional)
        """
        # Show spinner on button if provided
        if button:
            button.props("loading")
            button.disable()

        try:
            await self.service.create_racetime_room(
                user=self.user,
                organization_id=self.organization.id,
                match_id=match_id,
            )
            ui.notify("RaceTime room created", type="positive")
            await self.on_refresh()
        except Exception as e:
            logger.error("Failed to create RaceTime room: %s", e)
            ui.notify(f"Failed to create room: {str(e)}", type="negative")
        finally:
            # Remove spinner from button if provided
            if button:
                button.props(remove="loading")
                button.enable()

    async def sync_racetime_status(self, match_id: int) -> None:
        """Manually sync match status from RaceTime room."""
        try:
            result = await self.service.sync_racetime_room_status(
                user=self.user,
                organization_id=self.organization.id,
                match_id=match_id,
            )
            if result:
                ui.notify(
                    "Match status synced from RaceTime", type="positive"
                )
                await self.on_refresh()
            else:
                ui.notify("Failed to sync match status", type="negative")
        except ValueError as e:
            logger.error("Failed to sync RaceTime status: %s", e)
            ui.notify(f"Failed: {str(e)}", type="negative")
        except Exception as e:
            logger.error("Failed to sync RaceTime status: %s", e)
            ui.notify(f"Failed to sync status: {str(e)}", type="negative")

    def render_racetime(self, match: Match) -> None:
        """Render RaceTime.gg room information and controls."""
        with ui.column().classes("gap-2"):
            # Check if tournament has RaceTime integration
            has_racetime_bot = (
                getattr(match.tournament, "racetime_bot_id", None)
                is not None
            )

            if not has_racetime_bot:
                ui.label("—").classes("text-secondary")
                return

            # Show room link if room exists
            room = match.racetime_room
            if room:
                room_url = f"{settings.RACETIME_URL}/{room.slug}"
                with ui.link(target=room_url, new_tab=True).classes(
                    "text-primary"
                ):
                    with ui.row().classes("items-center gap-1"):
                        ui.icon("sports_esports").classes("text-sm")
                        ui.label("Join Room")

                # Show sync button for admins (if match not finished)
                if self.can_manage_tournaments and not match.finished_at:
                    ui.button(
                        icon="sync",
                        on_click=lambda m=match: self.sync_racetime_status(m.id),
                    ).classes("btn btn-sm").props(
                        "flat color=info size=sm"
                    ).tooltip(
                        "Sync status from RaceTime"
                    )

                # Show room status
                if match.racetime_invitational:
                    with ui.row().classes("items-center gap-1"):
                        ui.icon("lock", size="sm").classes("text-warning")
                        ui.label("Invite Only").classes(
                            "text-xs text-secondary"
                        )
            else:
                # No room created yet
                ui.label("No room").classes("text-secondary text-xs")

                # Show "Create Room" button for moderators
                if self.can_manage_tournaments:
                    # Create button reference first
                    button = ui.button(
                        "Create Room",
                        icon="add",
                    ).classes("btn btn-sm").props(
                        "flat color=positive size=sm"
                    )
                    
                    # Create async handler that captures button and match
                    async def handle_create_room(m_id=match.id, btn=button):
                        await self.create_racetime_room(m_id, btn)
                    
                    # Assign the async handler
                    button.on_click(handle_create_room)

            # Show countdown timer if room should open soon
            if match.scheduled_at and not room:
                room_open_minutes = getattr(
                    match.tournament, "room_open_minutes_before", 60
                )
                open_time = match.scheduled_at - timedelta(
                    minutes=room_open_minutes
                )
                now = datetime.now(timezone.utc)

                if now < open_time:
                    # Room not open yet - show countdown
                    time_until = open_time - now
                    hours = int(time_until.total_seconds() // 3600)
                    minutes = int((time_until.total_seconds() % 3600) // 60)

                    with ui.row().classes("items-center gap-1"):
                        ui.icon("schedule", size="sm").classes("text-info")
                        if hours > 0:
                            ui.label(
                                f"Opens in {hours}h {minutes}m"
                            ).classes("text-xs text-secondary")
                        else:
                            ui.label(f"Opens in {minutes}m").classes(
                                "text-xs text-secondary"
                            )
                elif now >= match.scheduled_at:
                    # Past scheduled time
                    pass
                else:
                    # Between open time and match time - should be open
                    with ui.row().classes("items-center gap-1"):
                        ui.icon("schedule", size="sm").classes(
                            "text-positive"
                        )
                        ui.label("Should be open").classes(
                            "text-xs text-secondary"
                        )

    async def open_edit_match_dialog(self, match: Match) -> None:
        """Open dialog to edit a match.
        
        Args:
            match: Match object to edit
        """

        async def on_save(title: str, scheduled_at, stream_id, comment):
            result = await self.service.update_match(
                self.user,
                self.organization.id,
                match.id,
                title=title,
                scheduled_at=scheduled_at,
                stream_channel_id=stream_id,
                comment=comment,
            )
            if result:
                ui.notify("Match updated", type="positive")
                await self.on_refresh()
            else:
                ui.notify("Failed to update match", type="negative")

        dialog = EditMatchDialog(
            match=match,
            organization_id=self.organization.id,
            on_save=on_save,
        )
        await dialog.show()

    def render_actions(self, match: Match, can_edit_matches: bool) -> None:
        """Render action buttons for moderators/tournament admins.
        
        Args:
            match: Match object to render actions for
            can_edit_matches: Whether user can edit matches
        """
        # Check if match is from SpeedGaming (read-only)
        is_speedgaming = (
            hasattr(match, "speedgaming_episode_id")
            and match.speedgaming_episode_id
        )

        if is_speedgaming:
            # For SpeedGaming matches, show nothing (badge in Match column is enough)
            ui.label("—").classes("text-secondary")
        elif can_edit_matches:
            with ui.row().classes("gap-1"):
                ui.button(
                    icon="edit",
                    on_click=lambda m=match: self.open_edit_match_dialog(m),
                ).classes("btn btn-sm").props(
                    "flat color=primary size=sm"
                ).tooltip(
                    "Edit match"
                )
        else:
            ui.label("—").classes("text-secondary")
