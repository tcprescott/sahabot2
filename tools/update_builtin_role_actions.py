"""
Update built-in role actions to match current definitions.

This script updates the actions field of existing built-in roles to match
the current definitions in authorization/builtin_roles.py.

Use this after modifying the REGULAR_ORG_BUILTIN_ROLES or SYSTEM_ORG_BUILTIN_ROLES
definitions to update existing organizations.
"""

import asyncio
import logging
import sys
from pathlib import Path

# Add parent directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from tortoise import Tortoise

from config import settings
from models import Organization
from models.authorization import OrganizationRole  # Use new authorization model
from application.authorization.builtin_roles import (
    REGULAR_ORG_BUILTIN_ROLES,
    SYSTEM_ORG_BUILTIN_ROLES,
)

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def update_builtin_role_actions():
    """Update actions for all built-in roles."""
    logger.info("=" * 60)
    logger.info("Updating Built-in Role Actions")
    logger.info("=" * 60)
    logger.info("")

    # Initialize database
    await Tortoise.init(db_url=settings.database_url, modules={"models": ["models"]})

    # Get all organizations
    organizations = await Organization.all()
    logger.info("Found %s organizations to process", len(organizations))
    logger.info("")

    total_updated = 0
    total_skipped = 0

    for org in organizations:
        logger.info("Updating roles for organization '%s' (id=%s)...", org.name, org.id)

        # Determine which built-in roles to use based on organization type
        if org.id == -1:
            builtin_definitions = SYSTEM_ORG_BUILTIN_ROLES
        else:
            builtin_definitions = REGULAR_ORG_BUILTIN_ROLES

        org_updated = 0
        org_skipped = 0

        for role_def in builtin_definitions:
            # Find existing role
            role = await OrganizationRole.get_or_none(
                organization_id=org.id, name=role_def.name
            )

            if not role:
                logger.warning(
                    "  - Role '%s' not found (should have been created by backfill)",
                    role_def.name,
                )
                continue

            # Check if actions need updating
            current_actions = set(role.actions or [])
            new_actions = set(role_def.actions)

            if current_actions == new_actions:
                logger.info("  - %s: No changes needed", role_def.name)
                org_skipped += 1
            else:
                # Update actions
                role.actions = role_def.actions
                await role.save()

                added = new_actions - current_actions
                removed = current_actions - new_actions

                logger.info("  - %s: Updated", role_def.name)
                if added:
                    logger.info("    Added: %s", ", ".join(sorted(added)))
                if removed:
                    logger.info("    Removed: %s", ", ".join(sorted(removed)))

                org_updated += 1

        logger.info(
            "  Organization total: %s updated, %s skipped", org_updated, org_skipped
        )
        logger.info("")

        total_updated += org_updated
        total_skipped += org_skipped

    logger.info("=" * 60)
    logger.info("Update complete!")
    logger.info("  - Organizations processed: %s", len(organizations))
    logger.info("  - Roles updated: %s", total_updated)
    logger.info("  - Roles unchanged: %s", total_skipped)
    logger.info("=" * 60)

    await Tortoise.close_connections()


if __name__ == "__main__":
    asyncio.run(update_builtin_role_actions())
