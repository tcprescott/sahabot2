from tortoise import BaseDBAsyncClient

RUN_IN_TRANSACTION = True


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE `users` ADD `racetime_id` VARCHAR(255) UNIQUE;
        ALTER TABLE `users` ADD `racetime_name` VARCHAR(255);
        ALTER TABLE `users` ADD `racetime_access_token` LONGTEXT;
        CREATE INDEX `idx_users_racetime_id` ON `users` (`racetime_id`);"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        DROP INDEX `idx_users_racetime_id` ON `users`;
        ALTER TABLE `users` DROP COLUMN `racetime_access_token`;
        ALTER TABLE `users` DROP COLUMN `racetime_name`;
        ALTER TABLE `users` DROP COLUMN `racetime_id`;"""
