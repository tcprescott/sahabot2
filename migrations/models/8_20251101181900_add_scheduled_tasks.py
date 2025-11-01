from tortoise import BaseDBAsyncClient

RUN_IN_TRANSACTION = True


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        CREATE TABLE IF NOT EXISTS `scheduled_tasks` (
    `id` INT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    `name` VARCHAR(255) NOT NULL,
    `description` LONGTEXT,
    `task_type` SMALLINT NOT NULL COMMENT 'RACETIME_OPEN_ROOM: 1\nCUSTOM: 99',
    `schedule_type` SMALLINT NOT NULL COMMENT 'INTERVAL: 1\nCRON: 2\nONE_TIME: 3',
    `interval_seconds` INT,
    `cron_expression` VARCHAR(255),
    `scheduled_time` DATETIME(6),
    `task_config` JSON NOT NULL,
    `is_active` BOOL NOT NULL DEFAULT 1,
    `last_run_at` DATETIME(6),
    `next_run_at` DATETIME(6),
    `last_run_status` VARCHAR(50),
    `last_run_error` LONGTEXT,
    `created_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    `updated_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
    `organization_id` INT NOT NULL,
    `created_by_id` INT,
    CONSTRAINT `fk_schedule_organiza_d9d3e8a9` FOREIGN KEY (`organization_id`) REFERENCES `organization` (`id`) ON DELETE CASCADE,
    CONSTRAINT `fk_schedule_user_a5b2c7d3` FOREIGN KEY (`created_by_id`) REFERENCES `user` (`id`) ON DELETE SET NULL,
    KEY `idx_scheduled_organization_active` (`organization_id`, `is_active`),
    KEY `idx_scheduled_next_run_active` (`next_run_at`, `is_active`)
) CHARACTER SET utf8mb4;"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        DROP TABLE IF EXISTS `scheduled_tasks`;"""
