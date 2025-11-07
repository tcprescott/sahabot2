"""
Built-in racetime chat command handlers.

This module provides dynamic command handlers for common racetime chat commands.
These handlers can be referenced by database commands via the handler_name field.
"""

import logging
from typing import Optional
from models import User, RacetimeChatCommand
from .sm_handlers import SM_HANDLERS

logger = logging.getLogger(__name__)


async def handle_help(
    _command: RacetimeChatCommand,
    _args: list[str],
    _racetime_user_id: str,
    _race_data: dict,
    _user: Optional[User],
) -> str:
    """
    Handle the !help command.

    Returns static help text.
    """
    return (
        "Available commands: "
        "!help (show this message), "
        "!status (race status), "
        "!race (race info), "
        "!time (your finish time), "
        "!entrants (list entrants by status)"
    )


async def handle_status(
    _command: RacetimeChatCommand,
    _args: list[str],
    _racetime_user_id: str,
    _race_data: dict,
    _user: Optional[User],
) -> str:
    """
    Handle the !status command.

    Returns current race status and entrant count.
    """
    status_value = _race_data.get('status', {}).get('value', 'unknown')
    entrants = _race_data.get('entrants', [])
    entrant_count = len(entrants)

    # Map status values to human-readable text
    status_text_map = {
        'open': 'Open',
        'invitational': 'Invitational',
        'pending': 'Pending',
        'in_progress': 'In Progress',
        'finished': 'Finished',
        'cancelled': 'Cancelled',
    }
    status_text = status_text_map.get(status_value, status_value.replace('_', ' ').title())

    return f'Race Status: {status_text} | Entrants: {entrant_count}'


async def handle_race_info(
    _command: RacetimeChatCommand,
    _args: list[str],
    _racetime_user_id: str,
    _race_data: dict,
    _user: Optional[User],
) -> str:
    """
    Handle the !race command.

    Returns race goal and info.
    """
    goal_name = _race_data.get('goal', {}).get('name', 'No goal set')
    info_text = _race_data.get('info', '')

    if info_text:
        return f'Goal: {goal_name} | Info: {info_text}'
    return f'Goal: {goal_name}'


async def handle_time(
    _command: RacetimeChatCommand,
    _args: list[str],
    _racetime_user_id: str,
    _race_data: dict,
    _user: Optional[User],
) -> str:
    """
    Handle the !time command.

    Shows the user's finish time or race time if still running.
    """
    entrants = _race_data.get('entrants', [])

    # Find the user in entrants
    user_entrant = None
    for entrant in entrants:
        if entrant.get('user', {}).get('id') == _racetime_user_id:
            user_entrant = entrant
            break

    if not user_entrant:
        return "You are not in this race."

    # Check if user has finished
    finish_time = user_entrant.get('finish_time')
    if finish_time:
        # Format finish time (it's a timedelta in ISO format)
        return f"Your finish time: {finish_time}"

    # User hasn't finished yet - show race time
    status_value = _race_data.get('status', {}).get('value', '')
    if status_value == 'in_progress':
        # Race is in progress
        started_at = _race_data.get('started_at')
        if started_at:
            return "Race is in progress. You haven't finished yet."
        return "Race hasn't started yet."

    return "Race hasn't started yet."


async def handle_entrants(
    _command: RacetimeChatCommand,
    _args: list[str],
    _racetime_user_id: str,
    _race_data: dict,
    _user: Optional[User],
) -> str:
    """
    Handle the !entrants command.

    Lists all entrants grouped by status (ready, not ready, finished, DNF).
    """
    entrants = _race_data.get('entrants', [])

    if not entrants:
        return "No entrants in this race."

    # Group by status
    ready = []
    not_ready = []
    finished = []
    dnf = []

    for entrant in entrants:
        username = entrant.get('user', {}).get('name', 'Unknown')
        status_value = entrant.get('status', {}).get('value', '')

        if status_value == 'ready':
            ready.append(username)
        elif status_value == 'not_ready':
            not_ready.append(username)
        elif status_value == 'done':
            finished.append(username)
        elif status_value == 'dnf':
            dnf.append(username)

    # Build response
    parts = []
    if ready:
        parts.append(f"Ready ({len(ready)}): {', '.join(ready)}")
    if not_ready:
        parts.append(f"Not Ready ({len(not_ready)}): {', '.join(not_ready)}")
    if finished:
        parts.append(f"Finished ({len(finished)}): {', '.join(finished)}")
    if dnf:
        parts.append(f"DNF ({len(dnf)}): {', '.join(dnf)}")

    if not parts:
        return f"Total entrants: {len(entrants)}"

    return " | ".join(parts)


async def handle_mystery(
    _command: RacetimeChatCommand,
    _args: list[str],
    _racetime_user_id: str,
    _race_data: dict,
    _user: Optional[User],
) -> str:
    """
    Handle the !mystery command.

    Generates a mystery seed from a named mystery preset.

    Args:
        _command: Command configuration
        _args: Command arguments (preset name)
        _racetime_user_id: RaceTime.gg user ID
        _race_data: Race data
        _user: Authenticated user (if any)

    Returns:
        Response message with seed URL or error
    """
    from application.services.randomizer.alttpr_mystery_service import ALTTPRMysteryService

    if not _args:
        return "Usage: !mystery <preset_name>"

    if not _user:
        return "You must be authenticated to generate mystery seeds."

    preset_name = _args[0]

    try:
        service = ALTTPRMysteryService()
        result, description = await service.generate_from_preset_name(
            mystery_preset_name=preset_name,
            user_id=_user.id,
            tournament=True,
            spoilers='off'
        )

        # Format description
        desc_parts = []
        if 'preset' in description:
            desc_parts.append(f"Preset: {description['preset']}")
        if 'subweight' in description:
            desc_parts.append(f"Subweight: {description['subweight']}")
        if 'entrance' in description and description['entrance'] != 'none':
            desc_parts.append(f"Entrance: {description['entrance']}")
        if 'customizer' in description:
            desc_parts.append("Customizer: enabled")

        desc_text = " | ".join(desc_parts) if desc_parts else "Mystery seed generated"

        return f"Mystery seed generated! {result.url} | {desc_text} | Hash: {result.hash_id}"

    except ValueError as e:
        logger.error("Mystery generation error: %s", str(e))
        return f"Error: {str(e)}"
    except PermissionError as e:
        logger.error("Mystery permission error: %s", str(e))
        return f"Error: {str(e)}"
    except Exception as e:
        logger.exception("Unexpected error generating mystery seed")
        return f"An error occurred generating mystery seed: {str(e)}"


async def handle_custommystery(
    _command: RacetimeChatCommand,
    _args: list[str],
    _racetime_user_id: str,
    _race_data: dict,
    _user: Optional[User],
) -> str:
    """
    Handle the !custommystery command.

    Generates a mystery seed from inline mystery weights (YAML format).

    Note: This is a placeholder - actual implementation would require
    parsing YAML from chat which is not practical. Users should upload
    mystery presets via the web UI instead.

    Returns:
        Informational message
    """
    return (
        "To use custom mystery weights, please upload your mystery YAML file via the web UI "
        "at /presets, then use !mystery <preset_name>"
    )


async def handle_avianart(
    _command: RacetimeChatCommand,
    _args: list[str],
    _racetime_user_id: str,
    _race_data: dict,
    _user: Optional[User],
) -> str:
    """
    Handle the !avianart command.

    Generates an Avianart door randomizer seed for racing.

    Args:
        _command: Command configuration
        _args: Command arguments (preset name)
        _racetime_user_id: RaceTime.gg user ID
        _race_data: Race data
        _user: Authenticated user (if any)

    Returns:
        Response message with seed URL or error
    """
    from application.services.randomizer.avianart_service import AvianartService

    if not _args:
        return "Usage: !avianart <preset_name>"

    preset_name = _args[0]

    try:
        service = AvianartService()
        result = await service.generate(
            preset=preset_name,
            race=True
        )

        # Extract file select code for display
        file_select_code = result.metadata.get('file_select_code', [])
        code_text = '/'.join(file_select_code) if file_select_code else result.hash_id

        return f"Avianart seed generated! {result.url} | Code: {code_text} | Version: {result.metadata.get('version', 'unknown')}"

    except ValueError as e:
        logger.error("Avianart generation error: %s", str(e))
        return f"Error: {str(e)}"
    except TimeoutError as e:
        logger.error("Avianart generation timeout: %s", str(e))
        return "Error: Seed generation timed out. Please try again."
    except Exception as e:
        logger.exception("Unexpected error generating Avianart seed")
        return f"An error occurred generating Avianart seed: {str(e)}"


# Registry of all built-in handlers
BUILTIN_HANDLERS = {
    'handle_help': handle_help,
    'handle_status': handle_status,
    'handle_race_info': handle_race_info,
    'handle_time': handle_time,
    'handle_entrants': handle_entrants,
    'handle_mystery': handle_mystery,
    'handle_custommystery': handle_custommystery,
    'handle_avianart': handle_avianart,
}


def get_all_handlers() -> dict:
    """
    Get all available command handlers including SM-specific handlers.

    Returns:
        Dictionary of all handler functions
    """
    return {
        **BUILTIN_HANDLERS,
        **SM_HANDLERS,
    }
