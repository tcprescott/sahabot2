from tortoise import BaseDBAsyncClient

RUN_IN_TRANSACTION = True


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        CREATE TABLE IF NOT EXISTS `race_room_profiles` (
    `id` INT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    `name` VARCHAR(255) NOT NULL,
    `description` LONGTEXT,
    `start_delay` INT NOT NULL DEFAULT 15,
    `time_limit` INT NOT NULL DEFAULT 24,
    `streaming_required` BOOL NOT NULL DEFAULT 0,
    `auto_start` BOOL NOT NULL DEFAULT 1,
    `allow_comments` BOOL NOT NULL DEFAULT 1,
    `hide_comments` BOOL NOT NULL DEFAULT 0,
    `allow_prerace_chat` BOOL NOT NULL DEFAULT 1,
    `allow_midrace_chat` BOOL NOT NULL DEFAULT 1,
    `allow_non_entrant_chat` BOOL NOT NULL DEFAULT 1,
    `is_default` BOOL NOT NULL DEFAULT 0,
    `created_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    `updated_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
    `organization_id` INT NOT NULL,
    UNIQUE KEY `uid_race_room_p_organiz_5c181d` (`organization_id`, `name`),
    CONSTRAINT `fk_race_roo_organiza_d6f562d6` FOREIGN KEY (`organization_id`) REFERENCES `organization` (`id`) ON DELETE CASCADE
) CHARACTER SET utf8mb4 COMMENT='Reusable configuration profile for RaceTime race rooms.';
        ALTER TABLE `tournament` ADD `race_room_profile_id` INT;
        ALTER TABLE `tournament` DROP COLUMN `racetime_streaming_required`;
        ALTER TABLE `tournament` DROP COLUMN `racetime_allow_midrace_chat`;
        ALTER TABLE `tournament` DROP COLUMN `racetime_auto_start`;
        ALTER TABLE `tournament` DROP COLUMN `racetime_time_limit`;
        ALTER TABLE `tournament` DROP COLUMN `racetime_allow_prerace_chat`;
        ALTER TABLE `tournament` DROP COLUMN `racetime_allow_non_entrant_chat`;
        ALTER TABLE `tournament` DROP COLUMN `racetime_hide_comments`;
        ALTER TABLE `tournament` DROP COLUMN `racetime_allow_comments`;
        ALTER TABLE `tournament` DROP COLUMN `racetime_start_delay`;
        ALTER TABLE `tournament` ADD CONSTRAINT `fk_tourname_race_roo_fe571c52` FOREIGN KEY (`race_room_profile_id`) REFERENCES `race_room_profiles` (`id`) ON DELETE CASCADE;"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE `tournament` DROP FOREIGN KEY `fk_tourname_race_roo_fe571c52`;
        ALTER TABLE `tournament` ADD `racetime_streaming_required` BOOL NOT NULL DEFAULT 0;
        ALTER TABLE `tournament` ADD `racetime_allow_midrace_chat` BOOL NOT NULL DEFAULT 1;
        ALTER TABLE `tournament` ADD `racetime_auto_start` BOOL NOT NULL DEFAULT 1;
        ALTER TABLE `tournament` ADD `racetime_time_limit` INT NOT NULL DEFAULT 24;
        ALTER TABLE `tournament` ADD `racetime_allow_prerace_chat` BOOL NOT NULL DEFAULT 1;
        ALTER TABLE `tournament` ADD `racetime_allow_non_entrant_chat` BOOL NOT NULL DEFAULT 1;
        ALTER TABLE `tournament` ADD `racetime_hide_comments` BOOL NOT NULL DEFAULT 0;
        ALTER TABLE `tournament` ADD `racetime_allow_comments` BOOL NOT NULL DEFAULT 1;
        ALTER TABLE `tournament` ADD `racetime_start_delay` INT NOT NULL DEFAULT 15;
        ALTER TABLE `tournament` DROP COLUMN `race_room_profile_id`;
        DROP TABLE IF EXISTS `race_room_profiles`;"""


MODELS_STATE = (
    "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"
    "O1b21EUmZK3uf08tf/B1Dw5H0="
)
