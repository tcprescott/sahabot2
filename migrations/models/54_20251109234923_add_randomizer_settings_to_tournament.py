"""
Add randomizer settings to Tournament model.

NOTE: This migration was manually created due to lack of database access in development environment.
Normally, migrations should ALWAYS be generated using `poetry run aerich migrate --name "description"`.
The MODELS_STATE below was copied from the previous migration and may need to be regenerated
if there are issues applying it.
"""

from tortoise import BaseDBAsyncClient

RUN_IN_TRANSACTION = True


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE `tournament` ADD `randomizer` VARCHAR(50);
        ALTER TABLE `tournament` ADD `randomizer_preset_id` INT;
        ALTER TABLE `tournament` ADD CONSTRAINT `fk_tournament_randomizer_preset` FOREIGN KEY (`randomizer_preset_id`) REFERENCES `randomizer_presets` (`id`) ON DELETE SET NULL;
        CREATE INDEX `idx_tournament_randomizer_preset_id` ON `tournament` (`randomizer_preset_id`);"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE `tournament` DROP FOREIGN KEY `fk_tournament_randomizer_preset`;
        ALTER TABLE `tournament` DROP INDEX `idx_tournament_randomizer_preset_id`;
        ALTER TABLE `tournament` DROP COLUMN `randomizer_preset_id`;
        ALTER TABLE `tournament` DROP COLUMN `randomizer`;"""


# MODELS_STATE copied from previous migration - may need regeneration with `aerich migrate`
MODELS_STATE = (
    "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"
)
