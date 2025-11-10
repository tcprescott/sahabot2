#!/usr/bin/env python3
"""Fix test import paths after service reorganization."""

import re
from pathlib import Path

# Map old mock paths to new paths
MOCK_PATH_MAPPINGS = {
    # RaceTime services
    r"@patch\('racetime\.client\.RacetimeRoomService'\)": r"@patch('application.services.racetime.racetime_room_service.RacetimeRoomService')",
    r"patch\('racetime\.client\.RacetimeRoomService'\)": r"patch('application.services.racetime.racetime_room_service.RacetimeRoomService')",
    r"patch\('racetime\.client\.UserRepository'\)": r"patch('application.repositories.user_repository.UserRepository')",
    # Notification handlers
    r"patch\('application\.services\.notification_handlers\.discord_handler\.get_bot_instance'\)": r"patch('application.services.notifications.handlers.discord_handler.get_bot_instance')",
    # Discord services
    r"@patch\('application\.services\.discord_scheduled_event_service\.get_bot_instance'\)": r"@patch('application.services.discord.discord_scheduled_event_service.get_bot_instance')",
    r"patch\('application\.services\.discord_scheduled_event_service\.get_bot_instance'\)": r"patch('application.services.discord.discord_scheduled_event_service.get_bot_instance')",
    # Tournament services
    r"patch\('application\.services\.tournament_service\.Match'\)": r"patch('application.services.tournaments.tournament_service.Match')",
    r"patch\('application\.services\.tournament_service\.RacetimeBot'\)": r"patch('application.services.tournaments.tournament_service.RacetimeBot')",
    r"patch\('application\.services\.tournament_service\.aiohttp\.ClientSession'\)": r"patch('application.services.tournaments.tournament_service.aiohttp.ClientSession')",
    # Task scheduler service
    r"@patch\('application\.services\.task_scheduler_service\.": r"@patch('application.services.tasks.task_scheduler_service.",
    r"patch\('application\.services\.task_scheduler_service\.": r"patch('application.services.tasks.task_scheduler_service.",
}


def fix_test_file(file_path: Path) -> int:
    """Fix mock paths in a test file."""
    content = file_path.read_text()
    original_content = content
    replacements = 0

    for old_pattern, new_pattern in MOCK_PATH_MAPPINGS.items():
        new_content, count = re.subn(old_pattern, new_pattern, content)
        if count > 0:
            content = new_content
            replacements += count
            print(
                f"  {file_path.relative_to(file_path.parent.parent.parent)}: Replaced {count} occurrence(s) of '{old_pattern[:50]}...'"
            )

    if replacements > 0 and content != original_content:
        file_path.write_text(content)

    return replacements


def main():
    """Fix all test files."""
    script_dir = Path(__file__).parent
    tests_dir = script_dir.parent / "tests"
    total_replacements = 0
    files_updated = 0

    print("Scanning test files for outdated mock paths...\n")

    for test_file in tests_dir.rglob("test_*.py"):
        replacements = fix_test_file(test_file)
        if replacements > 0:
            files_updated += 1
            total_replacements += replacements

    print(f"\n{'='*60}")
    print(f"✅ Fixed {total_replacements} mock path(s) in {files_updated} file(s)")
    print(f"{'='*60}\n")

    if files_updated > 0:
        print("Next steps:")
        print("1. Review changes: git diff tests/")
        print("2. Run tests: poetry run pytest -v --tb=short")
        print(
            "3. Commit if successful: git add tests/ && git commit -m 'Fix test mock import paths'"
        )
    else:
        print("No mock paths needed updating!")


if __name__ == "__main__":
    main()
