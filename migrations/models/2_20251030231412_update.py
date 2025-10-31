from tortoise import BaseDBAsyncClient

RUN_IN_TRANSACTION = True


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        CREATE TABLE IF NOT EXISTS `global_settings` (
    `id` INT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    `key` VARCHAR(255) NOT NULL UNIQUE,
    `value` JSON NOT NULL,
    `description` LONGTEXT,
    `is_public` BOOL NOT NULL DEFAULT 0,
    `created_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    `updated_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
    KEY `idx_global_sett_key_4f323e` (`key`)
) CHARACTER SET utf8mb4 COMMENT='Global application settings stored as key-value pairs.';
        CREATE TABLE IF NOT EXISTS `organization_settings` (
    `id` INT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    `key` VARCHAR(255) NOT NULL,
    `value` JSON NOT NULL,
    `description` LONGTEXT,
    `created_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    `updated_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
    `organization_id` INT NOT NULL,
    UNIQUE KEY `uid_organizatio_organiz_c0166f` (`organization_id`, `key`),
    CONSTRAINT `fk_organiza_organiza_bfe206f7` FOREIGN KEY (`organization_id`) REFERENCES `organization` (`id`) ON DELETE CASCADE,
    KEY `idx_organizatio_key_feb1eb` (`key`),
    KEY `idx_organizatio_organiz_151b4e` (`organization_id`)
) CHARACTER SET utf8mb4 COMMENT='Organization-specific settings that override or extend global settings.';"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        DROP TABLE IF EXISTS `global_settings`;
        DROP TABLE IF EXISTS `organization_settings`;"""


MODELS_STATE = (
    "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"
)
