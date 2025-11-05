from tortoise import BaseDBAsyncClient

RUN_IN_TRANSACTION = True


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE `racer_verifications` ADD `categories` JSON NOT NULL DEFAULT ('[]');
        ALTER TABLE `racer_verifications` ADD UNIQUE INDEX `uid_racer_verif_organiz_0a1e57` (`organization_id`, `guild_id`, `role_id`);
        ALTER TABLE `racer_verifications` DROP COLUMN `category`;"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE `racer_verifications` ADD `category` VARCHAR(50) NOT NULL;
        ALTER TABLE `racer_verifications` DROP INDEX `uid_racer_verif_organiz_0a1e57`;
        ALTER TABLE `racer_verifications` DROP COLUMN `categories`;"""
