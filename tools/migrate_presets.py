#!/usr/bin/env python3
"""
Preset migration utility.

This tool helps migrate presets from the original Sahasrahbot file-based
system to the new database-backed system in SahaBot2.

Usage:
    python tools/migrate_presets.py --preset-dir /path/to/presets
    python tools/migrate_presets.py --file /path/to/preset.yaml --namespace official --name mypreset --randomizer alttpr
"""

import asyncio
import argparse
import logging
import sys
from pathlib import Path
from typing import Optional

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from tortoise import Tortoise
from config import settings
from application.services.preset_service import PresetService

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def init_db():
    """Initialize database connection."""
    await Tortoise.init(
        db_url=settings.database_url,
        modules={'models': [
            'models.user',
            'models.audit_log',
            'models.api_token',
            'models.match_schedule',
            'models.organizations',
            'models.organization_invite',
            'models.settings',
            'models.preset'
        ]}
    )
    logger.info("Database initialized")


async def close_db():
    """Close database connection."""
    await Tortoise.close_connections()
    logger.info("Database connection closed")


async def migrate_preset_file(
    preset_path: Path,
    namespace: str,
    preset_name: Optional[str] = None,
    randomizer: Optional[str] = None,
    owner_discord_id: Optional[int] = None
) -> bool:
    """
    Migrate a single preset file to the database.

    Args:
        preset_path: Path to the preset YAML file
        namespace: Namespace to create preset in
        preset_name: Preset name (defaults to filename without extension)
        randomizer: Randomizer type (defaults to parent directory name)
        owner_discord_id: Discord ID of namespace owner (optional)

    Returns:
        True if successful, False otherwise
    """
    if not preset_path.exists():
        logger.error("Preset file not found: %s", preset_path)
        return False

    # Default preset name to filename without extension
    if not preset_name:
        preset_name = preset_path.stem

    # Default randomizer to parent directory name
    if not randomizer:
        randomizer = preset_path.parent.name

    # Read preset content
    try:
        content = preset_path.read_text()
    except Exception as e:
        logger.error("Failed to read preset file %s: %s", preset_path, e)
        return False

    # Create or update preset
    service = PresetService()

    try:
        # Get or create namespace
        ns = await service.get_or_create_namespace(namespace)
        if owner_discord_id and not ns.owner_discord_id:
            ns.owner_discord_id = owner_discord_id
            await ns.save()

        # Check if preset exists
        existing = await service.get_preset(namespace, preset_name, randomizer)

        if existing:
            logger.info("Updating existing preset: %s/%s (%s)", namespace, preset_name, randomizer)
            success = await service.update_preset(existing, content=content)
            if success:
                logger.info("Successfully updated preset: %s/%s (%s)", namespace, preset_name, randomizer)
            else:
                logger.error("Failed to update preset: %s/%s (%s)", namespace, preset_name, randomizer)
            return success
        else:
            logger.info("Creating new preset: %s/%s (%s)", namespace, preset_name, randomizer)
            preset = await service.create_preset(
                namespace,
                preset_name,
                randomizer,
                content,
                user=None  # System migration, no user context
            )
            if preset:
                logger.info("Successfully created preset: %s/%s (%s)", namespace, preset_name, randomizer)
                return True
            else:
                logger.error("Failed to create preset: %s/%s (%s)", namespace, preset_name, randomizer)
                return False

    except Exception as e:
        logger.error("Error migrating preset %s: %s", preset_path, e, exc_info=True)
        return False


async def migrate_preset_directory(
    presets_dir: Path,
    namespace: str = "official",
    owner_discord_id: Optional[int] = None
) -> tuple[int, int]:
    """
    Migrate all presets from a directory structure.

    Expected structure:
        presets_dir/
            alttpr/
                preset1.yaml
                preset2.yaml
            smz3/
                preset1.yaml
            sm/
                preset1.yaml

    Args:
        presets_dir: Root directory containing presets
        namespace: Namespace to create presets in
        owner_discord_id: Discord ID of namespace owner (optional)

    Returns:
        Tuple of (success_count, failure_count)
    """
    if not presets_dir.exists() or not presets_dir.is_dir():
        logger.error("Presets directory not found or not a directory: %s", presets_dir)
        return 0, 0

    success_count = 0
    failure_count = 0

    # Find all YAML files
    for yaml_file in presets_dir.rglob("*.yaml"):
        # Randomizer is the parent directory name
        randomizer = yaml_file.parent.name

        # Skip if parent is the root presets directory
        if yaml_file.parent == presets_dir:
            logger.warning("Skipping file in root directory: %s", yaml_file)
            continue

        success = await migrate_preset_file(
            yaml_file,
            namespace,
            randomizer=randomizer,
            owner_discord_id=owner_discord_id
        )

        if success:
            success_count += 1
        else:
            failure_count += 1

    return success_count, failure_count


async def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Migrate presets from filesystem to database"
    )

    parser.add_argument(
        "--preset-dir",
        type=Path,
        help="Directory containing presets organized by randomizer"
    )

    parser.add_argument(
        "--file",
        type=Path,
        help="Single preset file to migrate"
    )

    parser.add_argument(
        "--namespace",
        type=str,
        default="official",
        help="Namespace to create presets in (default: official)"
    )

    parser.add_argument(
        "--name",
        type=str,
        help="Preset name (for --file mode, defaults to filename)"
    )

    parser.add_argument(
        "--randomizer",
        type=str,
        help="Randomizer type (for --file mode, defaults to parent directory)"
    )

    parser.add_argument(
        "--owner-discord-id",
        type=int,
        help="Discord ID of namespace owner (optional)"
    )

    args = parser.parse_args()

    if not args.preset_dir and not args.file:
        parser.error("Either --preset-dir or --file must be specified")

    # Initialize database
    await init_db()

    try:
        if args.file:
            # Migrate single file
            success = await migrate_preset_file(
                args.file,
                args.namespace,
                args.name,
                args.randomizer,
                args.owner_discord_id
            )
            if success:
                logger.info("Migration successful")
                sys.exit(0)
            else:
                logger.error("Migration failed")
                sys.exit(1)

        elif args.preset_dir:
            # Migrate directory
            success_count, failure_count = await migrate_preset_directory(
                args.preset_dir,
                args.namespace,
                args.owner_discord_id
            )

            logger.info(
                "Migration complete: %s successful, %s failed",
                success_count,
                failure_count
            )

            if failure_count > 0:
                sys.exit(1)
            else:
                sys.exit(0)

    finally:
        await close_db()


if __name__ == "__main__":
    asyncio.run(main())
