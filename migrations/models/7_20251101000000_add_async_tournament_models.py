from tortoise import BaseDBAsyncClient

RUN_IN_TRANSACTION = True


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        CREATE TABLE IF NOT EXISTS `async_tournaments` (
    `id` INT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    `name` VARCHAR(255) NOT NULL,
    `description` LONGTEXT,
    `is_active` BOOL NOT NULL  DEFAULT 1,
    `discord_channel_id` BIGINT  UNIQUE,
    `runs_per_pool` SMALLINT NOT NULL  DEFAULT 1,
    `created_at` DATETIME(6) NOT NULL  DEFAULT CURRENT_TIMESTAMP(6),
    `updated_at` DATETIME(6) NOT NULL  DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
    `organization_id` INT NOT NULL,
    CONSTRAINT `fk_async_to_organiza_0e7e5af4` FOREIGN KEY (`organization_id`) REFERENCES `organizations` (`id`) ON DELETE CASCADE
) CHARACTER SET utf8mb4;
CREATE TABLE IF NOT EXISTS `async_tournament_pools` (
    `id` INT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    `name` VARCHAR(255) NOT NULL,
    `description` LONGTEXT,
    `created_at` DATETIME(6) NOT NULL  DEFAULT CURRENT_TIMESTAMP(6),
    `updated_at` DATETIME(6) NOT NULL  DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
    `tournament_id` INT NOT NULL,
    UNIQUE KEY `uid_async_tourn_tournam_18fd8e` (`tournament_id`, `name`),
    CONSTRAINT `fk_async_to_async_to_a9d7e6bc` FOREIGN KEY (`tournament_id`) REFERENCES `async_tournaments` (`id`) ON DELETE CASCADE
) CHARACTER SET utf8mb4;
CREATE TABLE IF NOT EXISTS `async_tournament_permalinks` (
    `id` INT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    `url` VARCHAR(500) NOT NULL,
    `notes` LONGTEXT,
    `par_time` DOUBLE,
    `par_updated_at` DATETIME(6),
    `created_at` DATETIME(6) NOT NULL  DEFAULT CURRENT_TIMESTAMP(6),
    `updated_at` DATETIME(6) NOT NULL  DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
    `pool_id` INT NOT NULL,
    CONSTRAINT `fk_async_to_async_to_5b8e1e77` FOREIGN KEY (`pool_id`) REFERENCES `async_tournament_pools` (`id`) ON DELETE CASCADE
) CHARACTER SET utf8mb4;
CREATE TABLE IF NOT EXISTS `async_tournament_races` (
    `id` INT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    `discord_thread_id` BIGINT,
    `thread_open_time` DATETIME(6),
    `thread_timeout_time` DATETIME(6),
    `start_time` DATETIME(6),
    `end_time` DATETIME(6),
    `status` VARCHAR(50) NOT NULL  DEFAULT 'pending',
    `reattempted` BOOL NOT NULL  DEFAULT 0,
    `runner_notes` LONGTEXT,
    `runner_vod_url` VARCHAR(500),
    `score` DOUBLE,
    `score_updated_at` DATETIME(6),
    `created_at` DATETIME(6) NOT NULL  DEFAULT CURRENT_TIMESTAMP(6),
    `updated_at` DATETIME(6) NOT NULL  DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
    `permalink_id` INT NOT NULL,
    `tournament_id` INT NOT NULL,
    `user_id` INT NOT NULL,
    CONSTRAINT `fk_async_to_async_to_31a7e3f4` FOREIGN KEY (`permalink_id`) REFERENCES `async_tournament_permalinks` (`id`) ON DELETE CASCADE,
    CONSTRAINT `fk_async_to_async_to_a8c4e2d5` FOREIGN KEY (`tournament_id`) REFERENCES `async_tournaments` (`id`) ON DELETE CASCADE,
    CONSTRAINT `fk_async_to_users_3f8d7c16` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) CHARACTER SET utf8mb4;
CREATE TABLE IF NOT EXISTS `async_tournament_audit_logs` (
    `id` INT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    `action` VARCHAR(100) NOT NULL,
    `details` LONGTEXT,
    `created_at` DATETIME(6) NOT NULL  DEFAULT CURRENT_TIMESTAMP(6),
    `tournament_id` INT NOT NULL,
    `user_id` INT,
    CONSTRAINT `fk_async_to_async_to_b9e5f3a6` FOREIGN KEY (`tournament_id`) REFERENCES `async_tournaments` (`id`) ON DELETE CASCADE,
    CONSTRAINT `fk_async_to_users_4a9e8d27` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) CHARACTER SET utf8mb4;"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        DROP TABLE IF EXISTS `async_tournament_audit_logs`;
        DROP TABLE IF EXISTS `async_tournament_races`;
        DROP TABLE IF EXISTS `async_tournament_permalinks`;
        DROP TABLE IF EXISTS `async_tournament_pools`;
        DROP TABLE IF EXISTS `async_tournaments`;"""
