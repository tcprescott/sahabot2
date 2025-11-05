from tortoise import BaseDBAsyncClient

RUN_IN_TRANSACTION = True


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE `tournament` ADD `speedgaming_enabled` BOOL NOT NULL DEFAULT 0;
        ALTER TABLE `tournament` ADD `speedgaming_event_slug` VARCHAR(255);
        ALTER TABLE `matches` ADD `speedgaming_episode_id` INT UNIQUE;
        ALTER TABLE `users` ADD `is_placeholder` BOOL NOT NULL DEFAULT 0;
    """


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE `tournament` DROP COLUMN `speedgaming_enabled`;
        ALTER TABLE `tournament` DROP COLUMN `speedgaming_event_slug`;
        ALTER TABLE `matches` DROP COLUMN `speedgaming_episode_id`;
        ALTER TABLE `users` DROP COLUMN `is_placeholder`;
    """
