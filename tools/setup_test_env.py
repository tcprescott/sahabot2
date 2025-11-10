#!/usr/bin/env python3
"""
Test Environment Setup Script

This script sets up a complete testing environment for the GitHub Coding Agent
or local development/testing without requiring MySQL or external services.

Features:
- Creates SQLite database for testing
- Runs database migrations
- Generates mock data for testing
- Validates environment configuration

Usage:
    python setup_test_env.py [--skip-data] [--clear-data] [--preset tiny|small|medium|large]
"""

import asyncio
import argparse
import logging
import sys
from pathlib import Path

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent))

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def setup_environment():
    """
    Set up environment variables for testing.
    """
    env_test_file = Path(__file__).parent / ".env.test"

    if not env_test_file.exists():
        logger.error(".env.test file not found. Cannot set up test environment.")
        return False

    # Copy .env.test to .env if .env doesn't exist
    env_file = Path(__file__).parent / ".env"
    if not env_file.exists():
        logger.info("Creating .env from .env.test...")
        env_file.write_text(env_test_file.read_text())
        logger.info("✓ .env file created from .env.test")
    else:
        logger.info("✓ .env file already exists")

    return True


async def initialize_database():
    """
    Initialize the database with Tortoise ORM and run migrations.
    """
    logger.info("Initializing database...")

    try:
        from tortoise import Tortoise
        from config import settings
        from migrations.tortoise_config import get_model_modules

        logger.info("Using database: %s", settings.safe_database_url)

        # Initialize Tortoise ORM
        await Tortoise.init(
            db_url=settings.database_url,
            modules={"models": get_model_modules()},
            use_tz=True,
            timezone="UTC",
        )

        # Generate schemas (for testing with SQLite)
        logger.info("Generating database schemas...")
        await Tortoise.generate_schemas()

        logger.info("✓ Database initialized successfully")

        # Close connections
        await Tortoise.close_connections()
        return True

    except Exception as e:
        logger.error("Failed to initialize database: %s", e, exc_info=True)
        return False


async def generate_mock_data(preset: str = "tiny", clear_existing: bool = False):
    """
    Generate mock data for testing.

    Args:
        preset: Size preset for mock data generation (tiny, small, medium, large)
        clear_existing: Whether to clear existing data before generating
    """
    logger.info("Generating mock data with preset: %s...", preset)

    try:
        from tools.generate_mock_data import MockDataGenerator, PRESETS
        from tortoise import Tortoise
        from config import settings
        from migrations.tortoise_config import get_model_modules

        # Initialize database connection
        await Tortoise.init(
            db_url=settings.database_url,
            modules={"models": get_model_modules()},
            use_tz=True,
            timezone="UTC",
        )

        # Get preset configuration
        config = PRESETS.get(preset, PRESETS["tiny"])
        logger.info(
            "Generating data: %d users, %d orgs, %d tournaments...",
            config["num_users"],
            config["num_orgs"],
            config["num_tournaments"],
        )

        # Create generator and run
        generator = MockDataGenerator(
            num_users=config["num_users"],
            num_orgs=config["num_orgs"],
            num_tournaments=config["num_tournaments"],
            num_async_tournaments=config["num_async_tournaments"],
            num_matches_per_tournament=config["num_matches_per_tournament"],
            clear_existing=clear_existing,
        )
        await generator.generate_all()

        logger.info("✓ Mock data generated successfully")

        # Close connections
        await Tortoise.close_connections()
        return True

    except Exception as e:
        logger.error("Failed to generate mock data: %s", e, exc_info=True)
        return False


async def validate_environment():
    """
    Validate that the test environment is properly configured.
    """
    logger.info("Validating test environment...")

    try:
        from config import settings

        # Check critical settings
        checks = [
            ("Database URL", settings.database_url is not None),
            ("Secret Key", bool(settings.SECRET_KEY)),
            ("Environment", settings.ENVIRONMENT == "testing"),
            ("Discord Bot Disabled", not settings.DISCORD_BOT_ENABLED),
        ]

        all_passed = True
        for check_name, passed in checks:
            status = "✓" if passed else "✗"
            logger.info("%s %s", status, check_name)
            if not passed:
                all_passed = False

        if all_passed:
            logger.info("✓ Environment validation passed")
        else:
            logger.warning("⚠ Some validation checks failed")

        return all_passed

    except Exception as e:
        logger.error("Failed to validate environment: %s", e, exc_info=True)
        return False


async def main():
    """
    Main entry point for test environment setup.
    """
    parser = argparse.ArgumentParser(description="Set up test environment for SahaBot2")
    parser.add_argument(
        "--skip-data", action="store_true", help="Skip mock data generation"
    )
    parser.add_argument(
        "--clear-data",
        action="store_true",
        help="Clear existing data before generating mock data (WARNING: destructive!)",
    )
    parser.add_argument(
        "--preset",
        choices=["tiny", "small", "medium", "large"],
        default="tiny",
        help="Mock data preset size (default: tiny)",
    )
    parser.add_argument(
        "--validate-only",
        action="store_true",
        help="Only validate environment without setup",
    )

    args = parser.parse_args()

    logger.info("=" * 60)
    logger.info("SahaBot2 Test Environment Setup")
    logger.info("=" * 60)

    # Validate only mode
    if args.validate_only:
        success = await validate_environment()
        sys.exit(0 if success else 1)

    # Step 1: Set up environment
    if not await setup_environment():
        logger.error("Failed to set up environment")
        sys.exit(1)

    # Step 2: Initialize database
    if not await initialize_database():
        logger.error("Failed to initialize database")
        sys.exit(1)

    # Step 3: Generate mock data (unless skipped)
    if not args.skip_data:
        if not await generate_mock_data(args.preset, args.clear_data):
            logger.error("Failed to generate mock data")
            sys.exit(1)
    else:
        logger.info("Skipping mock data generation (--skip-data)")

    # Step 4: Validate environment
    if not await validate_environment():
        logger.warning("Environment validation had warnings")

    # Import settings for database name check
    from config import settings

    logger.info("=" * 60)
    logger.info("✓ Test environment setup complete!")
    logger.info("=" * 60)
    logger.info("")
    logger.info("Next steps:")
    logger.info("  - Run tests: poetry run pytest")
    logger.info("  - Start dev server: ./start.sh dev")
    if settings.DB_NAME != ":memory:":
        logger.info("  - View database: sqlite3 test_%s.db", settings.DB_NAME)
    logger.info("")


if __name__ == "__main__":
    asyncio.run(main())
