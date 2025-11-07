from tortoise import BaseDBAsyncClient

RUN_IN_TRANSACTION = True


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE `racetime_bots` ADD `handler_class` VARCHAR(255) NOT NULL DEFAULT 'SahaRaceHandler' COMMENT 'Python class name for the race handler (e.g., ''ALTTPRRaceHandler'', ''SMRaceHandler'', ''SMZ3RaceHandler'')';
        DROP TABLE IF EXISTS `racetime_chat_commands`;"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE `racetime_bots` DROP COLUMN `handler_class`;
        CREATE TABLE IF NOT EXISTS `racetime_chat_commands` (
            `id` INT NOT NULL PRIMARY KEY AUTO_INCREMENT,
            `command` VARCHAR(50) NOT NULL,
            `description` TEXT,
            `response_type` INT NOT NULL,
            `response_text` TEXT,
            `handler_name` VARCHAR(100),
            `scope` INT NOT NULL,
            `racetime_bot_id` INT,
            `tournament_id` INT,
            `async_tournament_id` INT,
            `require_linked_account` BOOL NOT NULL DEFAULT 0,
            `cooldown_seconds` INT NOT NULL DEFAULT 0,
            `is_active` BOOL NOT NULL DEFAULT 1,
            `created_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
            `updated_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
            UNIQUE KEY `uid_racetime_c_racetim_d0ca39` (`racetime_bot_id`, `command`),
            UNIQUE KEY `uid_racetime_c_tournam_ec1f32` (`tournament_id`, `command`),
            UNIQUE KEY `uid_racetime_c_async_t_1b95de` (`async_tournament_id`, `command`),
            CONSTRAINT `fk_racetime_racetime_8d9c4e5c` FOREIGN KEY (`racetime_bot_id`) REFERENCES `racetime_bots` (`id`) ON DELETE CASCADE,
            CONSTRAINT `fk_racetime_tourname_b4f8c9e1` FOREIGN KEY (`tournament_id`) REFERENCES `tournaments` (`id`) ON DELETE CASCADE,
            CONSTRAINT `fk_racetime_async_to_c5d7a0f2` FOREIGN KEY (`async_tournament_id`) REFERENCES `async_tournaments` (`id`) ON DELETE CASCADE
        ) CHARACTER SET utf8mb4;"""


# NOTE: This migration was created manually because the development environment
# does not have access to `aerich migrate`. In a normal development workflow,
# you should ALWAYS use `aerich migrate --name "description"` to generate migrations.
# This ensures Aerich's MODELS_STATE tracking remains intact.
#
# MODELS_STATE intentionally omitted from this manual migration.
# After applying this migration, you MUST run `aerich migrate` to regenerate
# the MODELS_STATE and ensure schema tracking is correct.
