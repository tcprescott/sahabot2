#!/usr/bin/env python3
"""
Script to update service imports after reorganization.

This script updates all import statements from the old flat structure
to the new domain-organized structure.
"""

import re
from pathlib import Path
from typing import Dict

# Mapping of old imports to new imports
IMPORT_MAPPINGS: Dict[str, str] = {
    # Core services
    "application.services.user_service": "application.services.core.user_service",
    "application.services.audit_service": "application.services.core.audit_service",
    "application.services.settings_service": "application.services.core.settings_service",
    "application.services.rate_limit_service": "application.services.core.rate_limit_service",
    # Authorization services
    "application.services.authorization_service_v2": "application.services.authorization.authorization_service_v2",
    "application.services.ui_authorization_helper": "application.services.authorization.ui_authorization_helper",
    # Organization services
    "application.services.organization_service": "application.services.organizations.organization_service",
    "application.services.organization_invite_service": "application.services.organizations.organization_invite_service",
    "application.services.organization_request_service": "application.services.organizations.organization_request_service",
    "application.services.feature_flag_service": "application.services.organizations.feature_flag_service",
    # Tournament services
    "application.services.tournament_service": "modules.tournament.services.tournament_service",
    "application.services.async_tournament_service": "application.services.tournaments.async_tournament_service",
    "application.services.async_live_race_service": "application.services.tournaments.async_live_race_service",
    "application.services.tournament_usage_service": "modules.tournament.services.tournament_usage_service",
    "application.services.stream_channel_service": "modules.tournament.services.stream_channel_service",
    # Discord services
    "application.services.discord_service": "application.services.discord.discord_service",
    "application.services.discord_guild_service": "application.services.discord.discord_guild_service",
    "application.services.discord_scheduled_event_service": "application.services.discord.discord_scheduled_event_service",
    "application.services.discord_permissions_config": "application.services.discord.discord_permissions_config",
    # RaceTime services
    "application.services.racetime_service": "application.services.racetime.racetime_service",
    "application.services.racetime_api_service": "application.services.racetime.racetime_api_service",
    "application.services.racetime_bot_service": "application.services.racetime.racetime_bot_service",
    "application.services.racetime_chat_command_service": "application.services.racetime.racetime_chat_command_service",
    "application.services.racetime_room_service": "application.services.racetime.racetime_room_service",
    "application.services.race_room_profile_service": "application.services.racetime.race_room_profile_service",
    "application.services.racer_verification_service": "application.services.racetime.racer_verification_service",
    # Randomizer services
    "application.services.randomizer_preset_service": "application.services.randomizer.randomizer_preset_service",
    "application.services.preset_namespace_service": "application.services.randomizer.preset_namespace_service",
    # SpeedGaming services
    "application.services.speedgaming_service": "application.services.speedgaming.speedgaming_service",
    "application.services.speedgaming_etl_service": "application.services.speedgaming.speedgaming_etl_service",
    # Notification services
    "application.services.notification_service": "application.services.notifications.notification_service",
    "application.services.notification_processor": "application.services.notifications.notification_processor",
    "application.services.notification_handlers": "application.services.notifications.handlers",
    # Task services
    "application.services.task_scheduler_service": "application.services.tasks.task_scheduler_service",
    "application.services.task_handlers": "application.services.tasks.task_handlers",
    "application.services.builtin_tasks": "application.services.tasks.builtin_tasks",
    # Security services
    "application.services.api_token_service": "application.services.security.api_token_service",
}


def update_file_imports(file_path: Path) -> int:
    """
    Update imports in a single file.

    Returns:
        Number of replacements made
    """
    try:
        content = file_path.read_text()
        original_content = content
        replacements = 0

        for old_import, new_import in IMPORT_MAPPINGS.items():
            # Handle "from X import Y" style
            pattern = rf"from {re.escape(old_import)} import"
            replacement = f"from {new_import} import"
            new_content = re.sub(pattern, replacement, content)
            if new_content != content:
                replacements += content.count(f"from {old_import} import")
                content = new_content

            # Handle "import X" style (less common but possible)
            pattern = rf"import {re.escape(old_import)}"
            replacement = f"import {new_import}"
            new_content = re.sub(pattern, replacement, content)
            if new_content != content:
                replacements += content.count(f"import {old_import}")
                content = new_content

        if content != original_content:
            file_path.write_text(content)
            print(f"✓ Updated {file_path} ({replacements} replacements)")
            return replacements

        return 0
    except Exception as e:
        print(f"✗ Error updating {file_path}: {e}")
        return 0


def main():
    """Main function to update all Python files."""
    project_root = Path(__file__).parent.parent

    # Find all Python files (excluding venv, __pycache__, etc.)
    python_files = []
    for pattern in ["**/*.py"]:
        python_files.extend(project_root.glob(pattern))

    # Filter out unwanted directories
    excluded_dirs = {"__pycache__", ".venv", "venv", "node_modules", ".git"}
    python_files = [
        f
        for f in python_files
        if not any(excluded in f.parts for excluded in excluded_dirs)
    ]

    print(f"Found {len(python_files)} Python files to check")
    print("=" * 60)

    total_replacements = 0
    updated_files = 0

    for file_path in sorted(python_files):
        replacements = update_file_imports(file_path)
        if replacements > 0:
            total_replacements += replacements
            updated_files += 1

    print("=" * 60)
    print(f"✓ Updated {updated_files} files")
    print(f"✓ Made {total_replacements} import replacements")
    print("\nDone! Run tests to verify everything works.")


if __name__ == "__main__":
    main()
