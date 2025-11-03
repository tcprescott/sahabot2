from tortoise import BaseDBAsyncClient

RUN_IN_TRANSACTION = True


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        CREATE TABLE IF NOT EXISTS `discord_guilds` (
    `id` INT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    `guild_id` BIGINT NOT NULL UNIQUE,
    `guild_name` VARCHAR(255) NOT NULL,
    `guild_icon` VARCHAR(255),
    `verified_admin` BOOL NOT NULL DEFAULT 0,
    `is_active` BOOL NOT NULL DEFAULT 1,
    `bot_left_at` DATETIME(6),
    `created_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    `updated_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
    `linked_by_id` INT NOT NULL,
    `organization_id` INT NOT NULL,
    CONSTRAINT `fk_discord__users_e41a82d0` FOREIGN KEY (`linked_by_id`) REFERENCES `users` (`id`) ON DELETE CASCADE,
    CONSTRAINT `fk_discord__organiza_17af4234` FOREIGN KEY (`organization_id`) REFERENCES `organization` (`id`) ON DELETE CASCADE,
    KEY `idx_discord_gui_guild_i_8b0662` (`guild_id`)
) CHARACTER SET utf8mb4 COMMENT='Discord Guild linked to an organization.';
        CREATE TABLE IF NOT EXISTS `async_tournaments` (
    `id` INT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    `name` VARCHAR(255) NOT NULL,
    `description` LONGTEXT,
    `is_active` BOOL NOT NULL DEFAULT 1,
    `discord_channel_id` BIGINT UNIQUE,
    `runs_per_pool` SMALLINT NOT NULL DEFAULT 1,
    `created_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    `updated_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
    `organization_id` INT NOT NULL,
    CONSTRAINT `fk_async_to_organiza_ee102ca2` FOREIGN KEY (`organization_id`) REFERENCES `organization` (`id`) ON DELETE CASCADE
) CHARACTER SET utf8mb4 COMMENT='Async Tournament model.';
        CREATE TABLE IF NOT EXISTS `async_tournament_audit_logs` (
    `id` INT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    `action` VARCHAR(100) NOT NULL,
    `details` LONGTEXT,
    `created_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    `tournament_id` INT NOT NULL,
    `user_id` INT,
    CONSTRAINT `fk_async_to_async_to_108f7943` FOREIGN KEY (`tournament_id`) REFERENCES `async_tournaments` (`id`) ON DELETE CASCADE,
    CONSTRAINT `fk_async_to_users_08a6556a` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) CHARACTER SET utf8mb4 COMMENT='Audit log for async tournament actions.';
        CREATE TABLE IF NOT EXISTS `async_tournament_pools` (
    `id` INT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    `name` VARCHAR(255) NOT NULL,
    `description` LONGTEXT,
    `created_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    `updated_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
    `tournament_id` INT NOT NULL,
    UNIQUE KEY `uid_async_tourn_tournam_818000` (`tournament_id`, `name`),
    CONSTRAINT `fk_async_to_async_to_820235d6` FOREIGN KEY (`tournament_id`) REFERENCES `async_tournaments` (`id`) ON DELETE CASCADE
) CHARACTER SET utf8mb4 COMMENT='Pool of permalinks for an async tournament.';
        CREATE TABLE IF NOT EXISTS `async_tournament_permalinks` (
    `id` INT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    `url` VARCHAR(500) NOT NULL,
    `notes` LONGTEXT,
    `par_time` DOUBLE,
    `par_updated_at` DATETIME(6),
    `created_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    `updated_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
    `pool_id` INT NOT NULL,
    CONSTRAINT `fk_async_to_async_to_36a4e25a` FOREIGN KEY (`pool_id`) REFERENCES `async_tournament_pools` (`id`) ON DELETE CASCADE
) CHARACTER SET utf8mb4 COMMENT='Permalink/seed for an async tournament pool.';
        CREATE TABLE IF NOT EXISTS `async_tournament_races` (
    `id` INT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    `discord_thread_id` BIGINT,
    `thread_open_time` DATETIME(6),
    `thread_timeout_time` DATETIME(6),
    `start_time` DATETIME(6),
    `end_time` DATETIME(6),
    `status` VARCHAR(50) NOT NULL DEFAULT 'pending',
    `reattempted` BOOL NOT NULL DEFAULT 0,
    `runner_notes` LONGTEXT,
    `runner_vod_url` VARCHAR(500),
    `score` DOUBLE,
    `score_updated_at` DATETIME(6),
    `created_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    `updated_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
    `permalink_id` INT NOT NULL,
    `tournament_id` INT NOT NULL,
    `user_id` INT NOT NULL,
    CONSTRAINT `fk_async_to_async_to_1e2e1389` FOREIGN KEY (`permalink_id`) REFERENCES `async_tournament_permalinks` (`id`) ON DELETE CASCADE,
    CONSTRAINT `fk_async_to_async_to_8dcd165a` FOREIGN KEY (`tournament_id`) REFERENCES `async_tournaments` (`id`) ON DELETE CASCADE,
    CONSTRAINT `fk_async_to_users_36391f51` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) CHARACTER SET utf8mb4 COMMENT='Individual race in an async tournament.';
        ALTER TABLE `scheduled_tasks` MODIFY COLUMN `task_type` SMALLINT NOT NULL COMMENT 'EXAMPLE_LOG: 0\nRACETIME_OPEN_ROOM: 1\nCUSTOM: 99';"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE `scheduled_tasks` MODIFY COLUMN `task_type` SMALLINT NOT NULL COMMENT 'RACETIME_OPEN_ROOM: 1\nCUSTOM: 99';
        DROP TABLE IF EXISTS `discord_guilds`;
        DROP TABLE IF EXISTS `async_tournament_pools`;
        DROP TABLE IF EXISTS `async_tournament_permalinks`;
        DROP TABLE IF EXISTS `async_tournaments`;
        DROP TABLE IF EXISTS `async_tournament_races`;
        DROP TABLE IF EXISTS `async_tournament_audit_logs`;"""


MODELS_STATE = (
    "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"
)
