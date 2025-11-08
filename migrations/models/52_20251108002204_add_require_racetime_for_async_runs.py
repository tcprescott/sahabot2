from tortoise import BaseDBAsyncClient

RUN_IN_TRANSACTION = True


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE `async_tournaments` ADD `require_racetime_for_async_runs` BOOL NOT NULL DEFAULT 0 COMMENT 'Require RaceTime.gg account for async runs';"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE `async_tournaments` DROP COLUMN `require_racetime_for_async_runs`;"""


# NOTE: This migration was created manually because the development environment
# does not have access to a working `aerich migrate`. In a normal development workflow,
# you should ALWAYS use `aerich migrate --name "description"` to generate migrations.
# This ensures Aerich's MODELS_STATE tracking remains intact.
#
# MODELS_STATE intentionally omitted from this manual migration.
# After applying this migration in a production environment, you should run `aerich migrate`
# to regenerate the MODELS_STATE and ensure schema tracking is correct.
