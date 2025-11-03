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
    `created_by_id` INT,
    `organization_id` INT NOT NULL,
    CONSTRAINT `fk_schedule_users_a79c6e57` FOREIGN KEY (`created_by_id`) REFERENCES `users` (`id`) ON DELETE CASCADE,
    CONSTRAINT `fk_schedule_organiza_77d30839` FOREIGN KEY (`organization_id`) REFERENCES `organization` (`id`) ON DELETE CASCADE,
    KEY `idx_scheduled_t_organiz_c457dd` (`organization_id`, `is_active`),
    KEY `idx_scheduled_t_next_ru_282525` (`next_run_at`, `is_active`)
) CHARACTER SET utf8mb4 COMMENT='Scheduled task model.';"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        DROP TABLE IF EXISTS `scheduled_tasks`;"""


MODELS_STATE = (
    "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"
)
